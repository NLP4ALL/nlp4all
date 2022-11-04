"""Data Source routes"""

from flask import Blueprint
from flask_login import login_required

from nlp4all.controllers import DataSourceController

DataSourceRouter = Blueprint("datasource_controller", __name__)

DataSourceRouter.route("/", methods=["GET", "POST"])(
    login_required(DataSourceController.home)
)
DataSourceRouter.route("/create",
    methods=["GET", "POST"])(login_required(DataSourceController.create))
DataSourceRouter.route("/configure",
    methods=["GET", "POST"])(login_required(DataSourceController.configure))
DataSourceRouter.route("/save",
    methods=["GET", "POST"])(login_required(DataSourceController.save))
