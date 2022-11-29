"""
nlp4all module
"""

import os
from flask import Flask
from flask_login import LoginManager
from flask_cors import CORS
from flask_bcrypt import Bcrypt
from .config import get_config, Config
from .models import database
from .models import User
from .routes import Router

def load_user(user_id):
        """Loads a user from the database.

        Args:
            user_id (int): The id of the user to load.

        Returns:
        User: User object.
        """
        return User.query.get(int(user_id))

def create_app(env: str = "production") -> Flask:
    """Create the Flask app."""

    app = Flask(__name__, template_folder="views")
    conf: Config = get_config(env)
    app.secret_key = conf.get_secret()
    app.config.from_object(conf)
    os.environ.setdefault("SQLALCHEMY_DATABASE_URI", conf.SQLALCHEMY_DATABASE_URI)
    
    database.init_app(app)

    Router.run(app)

    CORS(app)

    # Bcrypt(app)
    login_manager = LoginManager(app)
    login_manager.user_loader(load_user)
    login_manager.login_message_category = "info"

    return app




