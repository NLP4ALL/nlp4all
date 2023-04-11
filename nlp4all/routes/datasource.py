"""Data Source routes"""

from flask import Blueprint
from flask_login import login_required

from ..controllers import DataSourceController

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
DataSourceRouter.route("/configure/<int:datasource_id>",
                       methods=["GET", "POST"])(DataSourceController.configure)  # type: ignore
DataSourceRouter.route("/configure/<int:datasource_id>/<string:step>",
                       methods=["GET", "POST"])(DataSourceController.configure)  # type: ignore
DataSourceRouter.route("/save",
                       methods=["GET", "POST"])(DataSourceController.save)
DataSourceRouter.route("/inspect/<int:datasource_id>",
                       methods=["GET", "POST"])(DataSourceController.inspect)
