"""
nlp4all module
"""

import os
from typing import Union

from flask import Flask
from flask_login import LoginManager
from flask_cors import CORS
# from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

from .helpers import database as dbhelper
from .helpers import nlp
from .config import get_config, Config
from .models.database import Base
from .models import load_user
from .routes import Router

db = SQLAlchemy(model_class = Base, engine_options={"future": True})
migrate = Migrate()

def create_app(env: Union[None, str] = None) -> Flask:
    """Create the Flask app."""

    app = Flask(__name__, template_folder="views", static_folder=None)
    conf: Config = get_config(env)
    app.config.from_object(conf)

    db.init_app(app)
    migrate.init_app(app, db)

    Router.run(app)

    CORS(app)

    # Bcrypt(app)
    login_manager = LoginManager(app)
    login_manager.user_loader(load_user)
    login_manager.login_message_category = "info"

    dbhelper.init_app(app)
    nlp.init_app(app)

    # in non-production environments, we want to be able to get a list of routes
    if conf.env != "production":
        from .helpers import development # pylint: disable=import-outside-toplevel
        app.add_url_rule('/api/help', methods = ['GET'], view_func=development.help_route)

    if conf.DB_BACKEND == "sqlite":
        from .helpers.database import model_cols_jsonb_to_json # pylint: disable=import-outside-toplevel
        app.logger.warning("{} {} {}".format( # pylint: disable=consider-using-f-string
            "Converting JSONB to JSON for SQLite backend",
            "This is ONLY for development purposes",
            "because SQLite does not support JSONB"))
        model_cols_jsonb_to_json(app, Base)

    return app
