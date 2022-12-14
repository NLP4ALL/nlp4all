"""Org admin / admin routes."""

from flask import Blueprint
from flask_login import login_required

from nlp4all.controllers import AdminController

AdminRouter = Blueprint("admin_controller", __name__)


@AdminRouter.before_request
@login_required
def before_request():
    """ Protect all of the admin endpoints."""


# AdminController.blueprint = AdminRouter
AdminRouter.route("/manage_categories", methods=["GET", "POST"])(
    AdminController.manage_categories
)
AdminRouter.route("/add_org", methods=["GET", "POST"])(AdminController.add_org)
