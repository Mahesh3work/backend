from flask import Flask, jsonify, request
from flask_smorest import Api
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from werkzeug.exceptions import HTTPException
import datetime, os

from blocklist import BLOCKLIST

from resources.users import blp as userBlueprint
from resources.sites import blp as sitesBlueprint
from resources.devices import blp as deviceBlueprint
from resources.orgs import blp as orgsBlueprint
from resources.roles import blp as rolesBlueprint
from resources.client import blp as clientBlueprint

app = Flask(__name__)
from werkzeug.middleware.proxy_fix import ProxyFix
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# CORS: allow extra origins from env (comma-separated). Required for production frontend URL.
_default_origins = [
    "http://localhost:4200",
    "http://127.0.0.1:4200",
   "https://device-xi.vercel.app",
   "https://frontend-dev-u3f3.onrender.com"

]
_extra_origins = os.getenv("CORS_ORIGINS", "").strip()
if _extra_origins:
    _default_origins = _default_origins + [o.strip() for o in _extra_origins.split(",") if o.strip()]

CORS(
    app,
    supports_credentials=True,
    origins=_default_origins,
    methods=["GET", "POST", "DELETE", "OPTIONS", "PUT"],
    allow_headers=["Content-Type", "Authorization", "X-Requested-With"],
)

app.config["PROPAGATE_EXCEPTIONS"] = True
app.config["API_TITLE"] = "Stores REST API"
app.config["API_VERSION"] = "1.0"
app.config["OPENAPI_VERSION"] = "3.0.2"
app.config["OPENAPI_URL_PREFIX"] = "/api"
app.config["OPENAPI_SWAGGER_UI_PATH"] = "/swagger-ui"
app.config["OPENAPI_SWAGGER_UI_URL"] = "https://cdn.jsdelivr.net/npm/swagger-ui-dist/"

# Use Environment Variable for JWT Secret Key
# app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", "fallback-secret-key")
app.config["JWT_SECRET_KEY"] =  "fallback-secret-key"

app.config["JWT_ACCESS_TOKEN_EXPIRES"] = datetime.timedelta(minutes=15)
app.config["JWT_REFRESH_TOKEN_EXPIRES"] = datetime.timedelta(days=7)

app.config["JWT_TOKEN_LOCATION"] = ["cookies", "headers"]
app.config["JWT_ACCESS_COOKIE_NAME"] = "access_token"
app.config["JWT_REFRESH_COOKIE_NAME"] = "refresh_token"
app.config["JWT_COOKIE_CSRF_PROTECT"] = False
# Cookie only sent over HTTPS when Secure=True. Set JWT_COOKIE_SECURE=0 if API is HTTP (e.g. behind reverse proxy that does SSL).
# app.config["JWT_COOKIE_SECURE"] = os.getenv("JWT_COOKIE_SECURE", "true").lower() in ("1", "true", "yes")
app.config["JWT_COOKIE_SECURE"] = True
app.config["JWT_COOKIE_SAMESITE"] = "None"
app.config["JWT_COOKIE_CSRF_PROTECT"] = False

api = Api(app, spec_kwargs={
    "components": {
        "securitySchemes": {
            "BearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT"
            }
        }
    },
    "security": [{"BearerAuth": []}]
})
jwt = JWTManager(app)


# default demonstration routes for lessons
@app.route("/", methods=["GET"])
def home():
    """Root route returning a welcome message."""
    return jsonify({"message": "API is running"}), 200







@app.route("/api/debug-token", methods=["GET"])
def debug_token():
    from flask import request
    result = {
        "authorization_header": None,
        "cookies": {},
    }

    auth = request.headers.get("Authorization")
    if auth:
        result["authorization_header"] = auth

        parts = auth.split()
        if len(parts) == 2:
            token = parts[1]
            try:
                import jwt as _pyjwt
                # unverified payload
                result["token_unverified"] = _pyjwt.decode(token, options={"verify_signature": False})
                try:
                    # verify signature using server secret via PyJWT
                    _pyjwt.decode(token, app.config.get("JWT_SECRET_KEY"), algorithms=["HS256"])
                    result["token_verified"] = True
                except Exception as ve:
                    # PyJWT can raise errors for non-string `sub` claims (Invalid subject string).
                    # Fallback to manual HMAC verification of the signature to avoid strict subject-type checks.
                    try:
                        import base64, hmac, hashlib

                        def _pad(s):
                            return s + '=' * (-len(s) % 4)

                        header_payload, sig = token.rsplit('.', 1)
                        sig_bytes = base64.urlsafe_b64decode(_pad(sig))
                        expected = hmac.new(app.config.get("JWT_SECRET_KEY").encode(), header_payload.encode(), hashlib.sha256).digest()
                        if hmac.compare_digest(sig_bytes, expected):
                            result["token_verified"] = True
                            result["verification_error"] = f"pyjwt_warning: {ve}"
                        else:
                            result["token_verified"] = False
                            result["verification_error"] = str(ve)
                            result["expected_sig_b64url"] = base64.urlsafe_b64encode(expected).rstrip(b'=').decode()
                            result["actual_sig_b64url"] = sig
                    except Exception as e2:
                        result["token_verified"] = False
                        result["verification_error"] = f"{ve}; fallback failed: {e2}"
            except Exception as e:
                result["token_unverified_error"] = str(e)

    # copy cookies into a plain dict
    try:
        for k, v in request.cookies.items():
            result["cookies"][k] = v
    except Exception:
        result["cookies"] = {}

    return jsonify(result), 200


@jwt.token_in_blocklist_loader
def check_if_token_in_blocklist(jwt_header, jwt_payload):
    jti = jwt_payload["jti"]
    return jti in BLOCKLIST

@jwt.revoked_token_loader
def revoked_token_callback(jwt_header, jwt_payload):
    return jsonify({"message": "The token has been revoked.", "error": "token_revoked"}, 401)

@jwt.invalid_token_loader
def invalid_token_callback(error):
    return jsonify({"message": "Signature verification failed.", "error": "invalid_token"}, 401)

@jwt.unauthorized_loader
def missing_token_callback(error):
    return jsonify({"message": "Request does not contain an access token.", "error": "authorization_required"}, 401)

api.register_blueprint(userBlueprint)
api.register_blueprint(sitesBlueprint)
api.register_blueprint(deviceBlueprint)
api.register_blueprint(orgsBlueprint)
api.register_blueprint(rolesBlueprint)
api.register_blueprint(clientBlueprint)

if __name__ == '__main__':
    port = int(os.getenv("PORT", 5000))
    app.run(debug=False, port=port, host='0.0.0.0')
