from flask import make_response, jsonify, request
from flask.views import MethodView
from flask_smorest import Blueprint, abort
from flask_jwt_extended import jwt_required, get_jwt_identity,get_jwt
from db import db


blp = Blueprint( "client", __name__, description="Operations on client", url_prefix="/api")

@blp.route("/client")
class client(MethodView):
    @jwt_required(locations=["cookies", "headers"])
    @blp.response(200)
    def get(self):
        print(">>> client ENDPOINT HIT <<<")
        user_id = get_jwt_identity()
        additional_claims = get_jwt()
        role = additional_claims.get("role")
        print(f"user id rolr is {role}")
        data = db.crud_client(
            user_id=user_id,
            action="READ"
        )

        return data, 200
    
    @jwt_required(locations=["cookies","headers"])
    @blp.response(200)
    def post(self):
        print(">>> client ENDPOINT post <<<")
        user_id = get_jwt_identity()
        claims = get_jwt()
        role = claims.get("role")
        print(f"user id rolr is {role}")
        data = db.crud_client(
            user_id=user_id,
            action="CREATE",
            client_name=request.json["client_name"],
            org_id=request.json["org_id"]
        )

        return data, 200
    
    @jwt_required(locations=["cookies","headers"])
    @blp.response(200)
    def delete(self):
        print(">>> client ENDPOINT delete <<<")
        user_id = get_jwt_identity()
        claims = get_jwt()
        role = claims.get("role")
        print(f"user id rolr is {role}")
        data = db.crud_client(
            user_id=user_id,
            action="DELETE",
            client_id=request.json["client_id"]
        )

        return data, 200
    
    @jwt_required(locations=["cookies","headers"])
    @blp.response(200)
    def put(self):
        print(">>> client ENDPOINT put <<<")
        user_id = get_jwt_identity()
        claims = get_jwt()
        role = claims.get("role")
        print(f"user id rolr is {role}")
        data = db.crud_client(
            user_id=user_id,
            action="UPDATE",
            client_id=request.json["client_id"],
            client_name=request.json["client_name"]
        )

        return data, 200

    
 