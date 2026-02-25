# flask_stores


REST API's to access database for clients to manage and access stores.

Uses alembic for database migrations and sqlite database for dev only soon gonna migrate to PostgreSQL.

# Docker run command
docker run -d -p 5000:5000 --name flask_app -e DATABASE_URI="" flask-gunicorn-app

# Avoiding "Too many connections" (MySQL)
# Total DB connections ≈ GUNICORN_WORKERS × DB_POOL_SIZE. Keep this below MySQL `max_connections`.
# Optional env vars: `DB_POOL_SIZE` (default 5, max 20), `GUNICORN_WORKERS` (default 2).
# Example: `-e DB_POOL_SIZE=3 -e GUNICORN_WORKERS=4`

# Production: "Request does not contain an access token" (401)
# 1. Add your frontend URL to CORS: set env CORS_ORIGINS (comma-separated), e.g.:
#    -e CORS_ORIGINS="https://your-domain.com,https://www.your-domain.com"
# 2. If the API is HTTP (no HTTPS): set -e JWT_COOKIE_SECURE=0 so cookies are sent.
# 3. Frontend must send requests with credentials (e.g. axios: withCredentials: true, or fetch: credentials: 'include').
# 4. Or send the token in the Authorization header: "Authorization: Bearer <access_token>".