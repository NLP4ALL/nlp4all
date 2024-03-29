"""
nlp4all module
"""

from typing import Union
from flask import Flask
from flask_login import LoginManager
from flask_cors import CORS
from flask_wtf.csrf import CSRFProtect
from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
# from flask_babel import Babel

from .helpers import database as dbhelper
from .helpers import nlp
from .helpers.mongo import Mongo
from .helpers.celery import celery_init_app
from .config import get_config, Config
from .database import Base, nlp_sa_meta
from .models import load_user
from .routes import Router

db: SQLAlchemy = SQLAlchemy(
    metadata=nlp_sa_meta,
    model_class=Base,
    engine_options={"future": True})
docdb: Mongo = Mongo()
migrate = Migrate()
csrf = CSRFProtect()

conf: Config = Config()


def create_app(env: Union[None, str] = None) -> Flask:
    """Create the Flask app."""
    global conf  # pylint: disable=global-statement
    app = Flask(__name__, template_folder="views", static_folder=None)
    conf = get_config(env, app)
    app.config.from_object(conf)

    db.init_app(app)
    migrate.init_app(app, db)
    # babel = Babel(app)

    Router.run(app)

    CORS(app)

    csrf.init_app(app)

    app.extensions['bcrypt'] = Bcrypt(app)
    login_manager = LoginManager(app)
    login_manager.user_loader(load_user)
    login_manager.login_message_category = "info"
    login_manager.refresh_view = "user_controller.reauth"  # type: ignore
    login_manager.needs_refresh_message = (
        u"To protect your account, please reauthenticate to access this page."
    )
    login_manager.needs_refresh_message_category = "info"

    dbhelper.init_app(app)
    # TODO: the connection probably doesn't need to exist for each request
    docdb.init_app(app)
    nlp.init_app(app)

    # in non-production environments, we want to be able to get a list of routes
    if conf.env != "production":
        from .helpers import development  # pylint: disable=import-outside-toplevel
        app.add_url_rule('/api/help', methods=['GET'], view_func=development.help_route)
        app.add_url_rule('/api/get_ds/<int:dsid>', methods=['GET'], view_func=development.load_data_source)

    if conf.DB_BACKEND == "sqlite":
        from .helpers.database import model_cols_jsonb_to_json  # pylint: disable=import-outside-toplevel
        app.logger.warning("{} {} {}".format(  # pylint: disable=consider-using-f-string
            "Converting JSONB to JSON for SQLite backend",
            "This is ONLY for development purposes",
            "because SQLite does not support JSONB"))
        model_cols_jsonb_to_json(app, Base)

    celery_init_app(app)

    return app
