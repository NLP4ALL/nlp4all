"""Site controller, general pages, about us, etc.""" # pylint: disable=invalid-name

from flask import send_from_directory, current_app
from .BaseController import BaseController

class SiteController(BaseController): # pylint: disable=too-few-public-methods
    """Site Controller"""

    view_subdir = "site"

    @classmethod
    def home(cls):
        """Home page"""
        return cls.render_template("home.html", title="Home")

    @classmethod
    def about(cls):
        """About page"""
        return cls.render_template("about.html", title="About")

    @classmethod
    def static_files(cls, filename):
        """Static file router"""
        return send_from_directory(current_app.config["STATIC_DIR"], filename)
