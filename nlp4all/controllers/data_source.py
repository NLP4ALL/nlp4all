"""Data sources."""  # pylint: disable=invalid-name

# @todo: SKELETON, NOT IMPLEMENTED
from flask import redirect, url_for

from .base import BaseController


class DataSourceController(BaseController):  # pylint: disable=too-few-public-methods
    """Data Source Controller"""

    view_subdir = "datasource"

    @classmethod
    def home(cls):
        """List of prepared data source"""
        return cls.render_template("data_source_list.html", title="My Data Sources")

    @classmethod
    def create(cls):
        """Upload / create page"""
        return cls.render_template("create_data_source.html", title="New Data Source")

    @classmethod
    def configure(cls):
        """Specify data fields"""
        return cls.render_template(
            "configure_data_source.html",
            title="Configure Data Source"
        )

    @classmethod
    def save(cls):
        """Save data source"""
        return redirect(url_for("data_source_controller.home"))
