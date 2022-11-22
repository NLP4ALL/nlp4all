"""Flask configuration"""

import os
from dotenv import load_dotenv

# Load environment variables from .flaskenv and .env file
basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, ".flaskenv"))
load_dotenv(os.path.join(basedir, ".env"))


class Config:  # pylint: disable=too-few-public-methods
    """Configuration for the Flask app."""

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = os.environ.get("SQLALCHEMY_DATABASE_URI", "sqlite:///data/site.db")
