from flask import make_response, jsonify, request
from flask.views import MethodView
from flask_smorest import Blueprint, abort
from flask_jwt_extended import jwt_required, get_jwt_identity,get_jwt

from db import db
from schemas import SiteSchema


blp = Blueprint("Sites", __name__, description="Operations on sites", url_prefix="/api")

@blp.route("/sites")
class Sites(MethodView):
    @jwt_required(locations=["cookies", "headers"])
    @blp.response(200)
    def get(self):
        print(">>> client ENDPOINT HIT <<<")
        user_id = get_jwt_identity()
        claims = get_jwt()
        role = claims.get("role")
        print(f"user id rolr is {role}")
        sites = db.crud_site(
            user_id=user_id,
            action="READ"
        )

        return sites, 200

    @jwt_required(locations=["cookies", "headers"])
    @blp.response(200)
    def post(self):
        print(">>> client ENDPOINT post <<<")
        user_id = get_jwt_identity()
        claims = get_jwt()
        role = claims.get("role")
        print(f"user id rolr is {role}")
        data = db.crud_site(
            user_id=user_id,
            action="CREATE",
            site_name=request.json["site_name"],
            client_id=request.json["client_id"]
        )

        return data, 200

    @jwt_required(locations=["cookies", "headers"])
    @blp.response(200)
    def delete(self):
        print(">>> client ENDPOINT delete <<<")
        user_id = get_jwt_identity()
        claims = get_jwt()
        role = claims.get("role")
        print(f"user id rolr is {role}")
        data = db.crud_site(
            user_id=user_id,
            action="DELETE",
            site_id=request.json["site_id"]
        )

        return data, 200

    @jwt_required(locations=["cookies", "headers"])
    @blp.response(200)
    def put(self):
        print(">>> client ENDPOINT put <<<")
        user_id = get_jwt_identity()
        claims = get_jwt()
        role = claims.get("role")
        print(f"user id rolr is {role}")
        data = db.crud_site(
            user_id=user_id,
            action="UPDATE",
            site_id=request.json["site_id"],
            site_name=request.json["site_name"]
        )

        return data, 200