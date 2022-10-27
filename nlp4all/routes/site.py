"""General site / page routes."""

from flask import Blueprint

from nlp4all.controllers import SiteController

SiteRouter = Blueprint("site_controller", __name__)

# AdminController.blueprint = AdminRouter
# SiteRouter.route('/', methods=["GET", "POST"])(SiteController.manage_categories)
# SiteRouter.route('/home', methods=["GET", "POST"])(SiteController.manage_categories)
SiteRouter.route("/about", methods=["GET", "POST"])(SiteController.about)


# if not logged in redirect to projects, we should have an actual "home" page

# @app.route("/")
# @app.route("/home")
# @app.route("/home/", methods=["GET", "POST"])

# @login_required
# def home():
#     """Home page"""
#     my_projects = get_user_projects(current_user)
#     return render_template("home.html", projects=my_projects)
