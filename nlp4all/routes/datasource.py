"""Data Source routes"""

from flask import Blueprint
from flask_login import login_required

from nlp4all.controllers import DataSourceController

DataSourceRouter = Blueprint("datasource_controller", __name__)


@DataSourceRouter.before_request
@login_required
def before_request():
    """ Protect all of the data source endpoints."""


DataSourceRouter.route("/", methods=["GET", "POST"])(
    DataSourceController.home
)
DataSourceRouter.route("/create",
                       methods=["GET", "POST"])(DataSourceController.create)
DataSourceRouter.route("/configure",
                       methods=["GET", "POST"])(DataSourceController.configure)
DataSourceRouter.route("/save",
                       methods=["GET", "POST"])(DataSourceController.save)
