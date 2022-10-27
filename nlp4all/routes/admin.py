"""Org admin / admin routes."""

from flask import Blueprint
from flask_login import login_required

from nlp4all.controllers import AdminController

AdminRouter = Blueprint('admin_controller', __name__)

# AdminController.blueprint = AdminRouter
AdminRouter.route('/manage_categories', methods=["GET", "POST"])(login_required(AdminController.manage_categories))
AdminRouter.route('/add_org', methods=["GET", "POST"])(login_required(AdminController.add_org))

