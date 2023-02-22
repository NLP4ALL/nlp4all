"""Router"""  # pylint: disable=invalid-name

from flask import Flask


class Router:  # pylint: disable=too-few-public-methods
    """Router"""

    @staticmethod
    def run(app: Flask):
        """Add routes to flask app."""
        # pylint: disable=import-outside-toplevel

        from .site import SiteRouter

        app.register_blueprint(SiteRouter, url_prefix="/")

        from .admin import AdminRouter

        app.register_blueprint(AdminRouter, url_prefix="/admin")

        from .user import UserRouter

        app.register_blueprint(UserRouter, url_prefix="/user")

        from .analyses import AnalysesRouter

        app.register_blueprint(AnalysesRouter, url_prefix="/analyses")

        from .project import ProjectRouter

        app.register_blueprint(ProjectRouter, url_prefix="/project")

        from .datasource import DataSourceRouter

        app.register_blueprint(DataSourceRouter, url_prefix="/datasource")

        # pylint: enable=import-outside-toplevel
