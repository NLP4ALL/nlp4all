"""Site controller, general pages, about us, etc.""" # pylint: disable=invalid-name

from flask import render_template


class SiteController: # pylint: disable=too-few-public-methods
    """Site Controller"""

    @classmethod
    def home(cls):
        """Home page"""
        return render_template("home.html", title="Home")

    @classmethod
    def about(cls):
        """About page"""
        return render_template("about.html", title="About")
