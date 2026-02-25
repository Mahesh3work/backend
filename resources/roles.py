from flask.views import MethodView
from flask_smorest import Blueprint
from flask_jwt_extended import jwt_required

from db import db

blp = Blueprint( "role", __name__, description="Operations on role", url_prefix="/api")


@blp.route("/role")
class RoleList(MethodView):

    @blp.response(200)
    @jwt_required(locations=["cookies", "headers"])
    def get(self):
        result = db.get_all_roles()
        return result, 200
