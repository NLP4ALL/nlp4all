"""Router"""

from flask import Flask


class Router:
    """Router"""

    @staticmethod
    def run(app: Flask):
        """Add routes to flask app."""

        from nlp4all.routes.site import SiteRouter

        app.register_blueprint(SiteRouter, url_prefix="/")

        from nlp4all.routes.admin import AdminRouter

        app.register_blueprint(AdminRouter, url_prefix="/admin")

        from nlp4all.routes.user import UserRouter

        app.register_blueprint(UserRouter, url_prefix="/user")

        from nlp4all.routes.analyses import AnalysesRouter

        app.register_blueprint(AnalysesRouter, url_prefix="/analyses")

        from nlp4all.routes.project import ProjectRouter

        app.register_blueprint(ProjectRouter, url_prefix="/project")
