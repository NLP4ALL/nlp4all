"""User info, registration, etc, routes."""

from flask import Blueprint
from flask_login import login_required

from nlp4all.controllers import UserController


UserRouter = Blueprint('user_controller', __name__)
UserController.blueprint = UserRouter
UserRouter.route('/account', methods=["GET", "POST"])(login_required(UserController.account))
UserRouter.route('/login', methods=["GET", "POST"])(UserController.login)
UserRouter.route('/logout')(login_required(UserController.logout))
UserRouter.route('/register', methods=["GET", "POST"])(UserController.register)
UserRouter.route('/register_imc', methods=["GET", "POST"])(UserController.register_imc)
UserRouter.route('/reset_password', methods=["GET", "POST"])(UserController.reset_request)
UserRouter.route('/reset_password/<token>', methods=["GET", "POST"])(UserController.reset_token)




# @app.route("/ATU", methods=["GET", "POST"])
# def imc():
#     """IMC registration start page"""
#     return redirect(url_for("register_imc"))
