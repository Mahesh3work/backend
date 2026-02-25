from flask import make_response, jsonify, request
from flask.views import MethodView
from flask_smorest import Blueprint, abort
from flask_jwt_extended import jwt_required, get_jwt_identity,get_jwt
from db import db


blp = Blueprint( "orgs", __name__, description="Operations on organizations", url_prefix="/api")

@blp.route("/organization")
class Organizations(MethodView):
    @jwt_required(locations=["cookies", "headers"])
    @blp.response(200)
    def get(self):
        print(">>> ORGANIZATION ENDPOINT HIT <<<")
        user_id = get_jwt_identity()
        claims = get_jwt()
        role = claims.get("role")
        print(f"user id rolr is {role}")
        data = db.get_organization(
            user_id=user_id,
            action="READ"
        )

        return data, 200
    
    @jwt_required(locations=["cookies", "headers"])
    @blp.response(200)
    def post(self):
        print(">>> ORGANIZATION ENDPOINT post <<<")
        user_id = get_jwt_identity()
        claims = get_jwt()
        role = claims.get("role")
        print(f"user id rolr is {role}")
        data = db.get_organization(
            user_id=user_id,
            action="CREATE",
            org_name=request.json["org_name"]
        )

        return data, 200
    
    @jwt_required(locations=["cookies", "headers"])
    @blp.response(200)
    def delete(self):
        print(">>> ORGANIZATION ENDPOINT delete <<<")
        user_id = get_jwt_identity()
        claims = get_jwt()
        role = claims.get("role")
        print(f"user id rolr is {role}")
        data = db.get_organization(
            user_id=user_id,
            action="DELETE",
            org_id=request.json["org_id"]
        )

        return data, 200
    
    @jwt_required(locations=["cookies", "headers"])
    @blp.response(200)
    def put(self):
        print(">>> ORGANIZATION ENDPOINT put <<<")
        user_id = get_jwt_identity()
        claims = get_jwt()
        role = claims.get("role")
        print(f"user id rolr is {role}")
        data = db.get_organization(
            user_id=user_id,
            action="UPDATE",
            org_id=request.json["org_id"],
            org_name=request.json["org_name"]
        )

        return data, 200
    

    

    
 