from flask import Blueprint
from flask_login import login_required

from nlp4all.controllers import ProjectController

ProjectRouter = Blueprint('project_controller', __name__)

ProjectRouter.route('/add_project', methods=["GET", "POST"])(login_required(ProjectController.add_project))
ProjectRouter.route('/project', methods=["GET", "POST"])(login_required(ProjectController.project))
