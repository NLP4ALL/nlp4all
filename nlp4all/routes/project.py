"""Project routes"""

from flask import Blueprint
from flask_login import login_required

from nlp4all.controllers import ProjectController

ProjectRouter = Blueprint("project_controller", __name__)

@ProjectRouter.before_request
@login_required
def before_request():
    """ Protect all of the project endpoints."""

ProjectRouter.route("/add_project", methods=["GET", "POST"])(
    ProjectController.add_project
)
ProjectRouter.route("/project", methods=["GET", "POST"])(ProjectController.project)
ProjectRouter.route("/home", methods=["GET", "POST"])(ProjectController.home)
