"""General site / page routes."""

from flask import Blueprint

from nlp4all.controllers import SiteController

SiteRouter = Blueprint("site_controller", __name__, static_url_path="")

# AdminController.blueprint = AdminRouter
SiteRouter.route('/', methods=["GET", "POST"])(SiteController.home)
SiteRouter.route("/about", methods=["GET", "POST"])(SiteController.about)

SiteRouter.route("/static/<path:filename>", methods=["GET"])(SiteController.static_files)
