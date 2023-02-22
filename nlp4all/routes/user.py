"""User info, registration, etc, routes."""

from flask import Blueprint
from flask_login import login_required

from ..controllers import UserController


UserRouter = Blueprint("user_controller", __name__)
UserController.blueprint = UserRouter
UserRouter.route("/account", methods=["GET", "POST"])(login_required(UserController.account))
UserRouter.route("/login", methods=["GET", "POST"])(UserController.login)
UserRouter.route("/logout")(UserController.logout)
UserRouter.route("/register", methods=["GET", "POST"])(UserController.register)
UserRouter.route("/reset_password", methods=["GET", "POST"])(UserController.reset_request)
UserRouter.route("/reset_password/<token>", methods=["GET", "POST"])(UserController.reset_token)


# @app.route("/ATU", methods=["GET", "POST"])
# def imc():
#     """IMC registration start page"""
#     return redirect(url_for("register_imc"))
