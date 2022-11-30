"""
nlp4all module
"""

import os

from flask import Flask, send_from_directory
from flask_login import LoginManager
from flask_cors import CORS
# from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

from .helpers import database as dbhelper
from .config import get_config, Config
from .models.database import Base
from .models import load_user
from .routes import Router

db = SQLAlchemy(model_class = Base)
migrate = Migrate()


def create_app(env: str = "production") -> Flask:
    """Create the Flask app."""

    app = Flask(__name__, template_folder="views")
    conf: Config = get_config(env)
    app.secret_key = conf.get_secret()
    app.config.from_object(conf)
    os.environ.setdefault("SQLALCHEMY_DATABASE_URI", conf.SQLALCHEMY_DATABASE_URI)

    db.init_app(app)
    migrate.init_app(app, db)

    Router.run(app)

    CORS(app)

    # Bcrypt(app)
    login_manager = LoginManager(app)
    login_manager.user_loader(load_user)
    login_manager.login_message_category = "info"

    dbhelper.init_app(app)

    if env != "production":
        from .helpers import development # pylint: disable=wrong-import-position
        app.add_url_rule('/api/help', methods = ['GET'], view_func=development.help_route)
    
    
    @app.route("/static/<path:filename>")
    def staticfiles(filename):
        """Static file router"""
        return send_from_directory(app.config["STATIC_DIR"], filename)

    return app
