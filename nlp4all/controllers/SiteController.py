"""Site controller, general pages, about us, etc."""

from flask import render_template

class SiteController:
    """Site Controller"""

    @classmethod
    def about(cls):
      """About page"""
      return render_template("about.html", title="About")