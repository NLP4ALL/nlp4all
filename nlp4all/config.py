"""Flask configuration"""

import os
import secrets
from pathlib import Path
# from dotenv import load_dotenv

def get_env_variable(name: str) -> str:
    """Get the environment variable or raise exception."""
    try:
        return os.environ[name]
    except KeyError as exc:
        message = f"Expected environment variable '{name}' not set."
        raise EnvironmentError(message) from exc

# # Load environment variables from .flaskenv and .env file
# basedir = os.path.abspath(os.path.dirname(__file__))
# load_dotenv(os.path.join(basedir, ".flaskenv"))
# load_dotenv(os.path.join(basedir, ".env"))

DB_URI = ""

try:
    DB_BACKEND = get_env_variable("DB_BACKEND")
except EnvironmentError:
    DB_BACKEND = "sqlite"

if DB_BACKEND == "postgres":
    pg_host = get_env_variable('POSTGRES_HOST')
    pg_user = get_env_variable('POSTGRES_USER')
    pg_pass = get_env_variable('POSTGRES_PASSWORD')
    pg_db = get_env_variable('POSTGRES_DB')
    URI_TEMPLATE = 'postgresql+psycopg2://{user}:{pw}@{url}/{db}'
    DB_URI = URI_TEMPLATE.format(
        user=pg_user,
        pw=pg_pass,
        url=pg_host,
        db=pg_db)

class Config: # pylint: disable=too-few-public-methods
    """Configuration for the Flask app."""
    SQLALCHEMY_WARN_20 = 1
    DEBUG = False
    TESTING = False
    SECRET_FILE_PATH = Path(".flask_secret")

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = DB_URI
    STATIC_DIR = Path(__file__).parent / "static"

    SPACY_MODEL_TYPES = {
        "small": "sm",
        #"medium": "md",
        #"large": "lg",

        # Note: Transformer versions require GPU
        #"transformer": "trf",
    }
    SPACY_MODEL_LANGUAGES = {
        "en": "en_core_web",
        "da": "da_core_news",
    }

    @staticmethod
    def spacy_model_name(language, model_type):
        """Get the spacy model name."""
        return Config.SPACY_MODEL_LANGUAGES[language] + "_" + Config.SPACY_MODEL_TYPES[model_type]

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

class LocalDevelopmentConfig(Config): # pylint: disable=too-few-public-methods
    """Configuration for the Flask app in testing."""
    SECRET_FILE_PATH = Path(".flask_secret_localdev")
    SQLALCHEMY_DATABASE_URI = "sqlite:///../data/nlp4all_dev.db"
    TESTING = True

class TestConfig(Config): # pylint: disable=too-few-public-methods
    """Configuration for the Flask app in testing."""
    SECRET_FILE_PATH = Path(".flask_secret_test")
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    TESTING = True


class ProductionConfig(Config): # pylint: disable=too-few-public-methods
    """Configuration for the Flask app in production."""


def get_config(env=None):
    """Get the configuration for the Flask app."""
    if env is None:
        try:
            env = get_env_variable('NLP4ALL_ENV')
        except EnvironmentError:
            env = 'production'
            print(f'env is not set, using: {env}')

    if env == 'production':
        if DB_URI == "":
            raise EnvironmentError('Cannot use SQLite in production')
        return ProductionConfig()

    if env == 'testing':
        return TestConfig()

    if env == 'development':
        if DB_URI == "":
            raise EnvironmentError('Cannot use SQLite in production')
        return DevelopmentConfig()

    if env == 'localdev':
        return LocalDevelopmentConfig()

    raise EnvironmentError(f'Unknown environment: {env}')

