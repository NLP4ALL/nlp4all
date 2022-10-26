"""
nlp4all module
"""
import secrets
import os
from pathlib import Path
from flask import Flask
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_cors import CORS
from .config import Config
# from flask_mail import Mail

app = Flask(__name__, template_folder="views")

os.environ.setdefault("SQLALCHEMY_DATABASE_URI", Config.SQLALCHEMY_DATABASE_URI)
app.config.from_object(Config)

from .models.database import db_session
from .models import User
from .routes import Router


# Load secret key from file, generate if not present
SECRET_FILE_PATH = Path(".flask_secret")
try:
    with SECRET_FILE_PATH.open("r", encoding="utf8") as secret_file:
        app.secret_key = secret_file.read()
except FileNotFoundError:
    # Let's create a cryptographically secure code in that file
    with SECRET_FILE_PATH.open("w", encoding="utf8") as secret_file:
        app.secret_key = secrets.token_hex(32)
        secret_file.write(app.secret_key)

app.session = db_session  # type: ignore

Router.run(app)

CORS(app)

# db = SQLAlchemy(app)
# bcrypt = Bcrypt(app)
login_manager = LoginManager(app)

@login_manager.user_loader
def load_user(user_id):
    """Loads a user from the database.

    Args:
        user_id (int): The id of the user to load.

    Returns:
       User: User object.
    """
    return User.query.get(int(user_id))

login_manager.login_message_category = "info"


# mail = Mail(app)

@app.teardown_appcontext
def shutdown_session(exception=None):
    db_session.remove()