"""General site / page routes."""

from flask import Blueprint

from nlp4all.controllers import SiteController

SiteRouter = Blueprint("site_controller", __name__)

# AdminController.blueprint = AdminRouter
SiteRouter.route('/', methods=["GET", "POST"])(SiteController.home)
SiteRouter.route("/about", methods=["GET", "POST"])(SiteController.about)