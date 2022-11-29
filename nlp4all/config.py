"""Flask configuration"""

import os
import secrets
from pathlib import Path
from dotenv import load_dotenv

def get_env_variable(name: str) -> str:
    """Get the environment variable or raise exception."""
    try:
        return os.environ[name]
    except KeyError:
        message = "Expected environment variable '{}' not set.".format(name)
        raise Exception(message)

# Load environment variables from .flaskenv and .env file
basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, ".flaskenv"))
load_dotenv(os.path.join(basedir, ".env"))


POSTGRES_URL = get_env_variable('POSTGRES_URL')
POSTGRES_USER = get_env_variable('POSTGRES_USER')
POSTGRES_PASSWORD = get_env_variable('POSTGRES_PASSWORD')
POSTGRES_DB = get_env_variable('POSTGRES_DB')


class Config: # pylint: disable=too-few-public-methods
    """Configuration for the Flask app."""

    DEBUG = False
    TESTING = False
    SECRET_FILE_PATH = Path(".flask_secret")

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    uri_template = 'postgresql+psycopg2://{user}:{pw}@{url}/{db}'
    SQLALCHEMY_DATABASE_URI = uri_template.format(
        user=POSTGRES_USER,
        pw=POSTGRES_PASSWORD,
        url=POSTGRES_URL,
        db=POSTGRES_DB)
    
    def get_secret(self) -> str:
        """Get the secret key for the app."""
        try:
            with self.SECRET_FILE_PATH.open("r", encoding="utf8") as secret_file:
                secret_key = secret_file.read()
        except FileNotFoundError:
            # Let's create a cryptographically secure code in that file
            with self.SECRET_FILE_PATH.open("w", encoding="utf8") as secret_file:
                secret_key = secrets.token_hex(32)
                secret_file.write(secret_key)

        return secret_key

class DevelopmentConfig(Config): # pylint: disable=too-few-public-methods
    """Configuration for the Flask app in development."""
    SECRET_FILE_PATH = Path(".flask_secret_dev")
    DEBUG = True


class TestConfig(Config): # pylint: disable=too-few-public-methods
    """Configuration for the Flask app in testing."""
    SECRET_FILE_PATH = Path(".flask_secret_test")
    TESTING = True


class ProductionConfig(Config): # pylint: disable=too-few-public-methods
    """Configuration for the Flask app in production."""
    pass


def get_config(env=None):
    if env is None:
        try:
            env = get_env_variable('ENV')
        except Exception:
            env = 'development'
            print('env is not set, using env:', env)

    if env == 'production':
        return ProductionConfig()
    elif env == 'test':
        return TestConfig()

    return DevelopmentConfig()