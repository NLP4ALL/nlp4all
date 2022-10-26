"""Router"""

from flask import Flask


class Router:
    """Router"""

    @staticmethod
    def run(app: Flask):
      from .user import UserRouter
      app.register_blueprint(UserRouter, url_prefix='/user')
      