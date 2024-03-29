"""Flask configuration"""

import typing as t
import os
import logging
import secrets
from pathlib import Path
# from dotenv import load_dotenv

if t.TYPE_CHECKING:
    from flask import Flask


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

try:
    MONGODB_HOST = get_env_variable("MONGODB_HOST")
    MONGO_INITDB_ROOT_USERNAME = get_env_variable("MONGO_INITDB_ROOT_USERNAME")
    MONGO_INITDB_ROOT_PASSWORD = get_env_variable("MONGO_INITDB_ROOT_PASSWORD")
except EnvironmentError:
    MONGODB_HOST = "document-store"
    MONGO_INITDB_ROOT_USERNAME = "nlp4all"
    MONGO_INITDB_ROOT_PASSWORD = "nlp4all"

if DB_BACKEND == "postgres":
    pg_host = get_env_variable('POSTGRES_HOST')
    pg_user = get_env_variable('POSTGRES_USER')
    pg_pass = get_env_variable('POSTGRES_PASSWORD')
    pg_db = get_env_variable('POSTGRES_DB')
    URI_TEMPLATE = 'postgresql+psycopg://{user}:{pw}@{url}/{db}'
    DB_URI = URI_TEMPLATE.format(
        user=pg_user,
        pw=pg_pass,
        url=pg_host,
        db=pg_db)

MQ_HOST = os.getenv("MQ_HOST", "rabbitmq")
CELERY_BROKER_URL = f"amqp://guest@{MQ_HOST}//"
CELERY_RESULT_BACKEND = f"rpc://guest@{MQ_HOST}//"


class Config:  # pylint: disable=too-few-public-methods
    """Configuration for the Flask app."""
    SQLALCHEMY_WARN_20 = 1
    DEBUG = False
    TESTING = False
    SECRET_FILE_PATH = Path(".flask_secret")
    DB_BACKEND = DB_BACKEND
    LOG_LEVEL = logging.WARNING
    DATA_UPLOAD_DIR: str = 'data'

    # Security
    BCRYPT_LOG_ROUNDS: int = 12
    BCRYPT_HASH_PREFIX: str = "2b"
    BCRYPT_HANDLE_LONG_PASSWORDS: bool = True

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = DB_URI
    STATIC_DIR = "static"

    # Celery
    CELERY: dict = dict(
        broker_url=CELERY_BROKER_URL,
        result_backend=CELERY_RESULT_BACKEND,
        task_ignore_result=True,
    )

    SPACY_MODEL_TYPES = {
        "small": "sm",
        # "medium": "md",
        # "large": "lg",

        # Note: Transformer versions require GPU
        # "transformer": "trf",
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

    def __init__(self, env=None):
        """Initialize the configuration."""
        self.SECRET_KEY = self.get_secret()  # pylint: disable=invalid-name
        self.env = env
        self._set_log_level()

    def _set_log_level(self):
        """Set the log level."""
        logging.basicConfig(level=self.LOG_LEVEL)


class DevelopmentConfig(Config):  # pylint: disable=too-few-public-methods
    """Configuration for the Flask app in development."""
    SECRET_FILE_PATH = Path(".flask_secret_dev")
    DEBUG = True
    LOG_LEVEL = logging.DEBUG


class LocalDevelopmentConfig(Config):  # pylint: disable=too-few-public-methods
    """Configuration for the Flask app in testing."""
    SECRET_FILE_PATH = Path(".flask_secret_localdev")
    SQLALCHEMY_DATABASE_URI = "sqlite:///../data/nlp4all_dev.db"
    DEBUG = True
    LOG_LEVEL = logging.DEBUG


class TestConfig(Config):  # pylint: disable=too-few-public-methods
    """Configuration for the Flask app in testing."""
    SECRET_FILE_PATH = Path(".flask_secret_test")
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    TESTING = True
    LOG_LEVEL = logging.DEBUG


class ProductionConfig(Config):  # pylint: disable=too-few-public-methods
    """Configuration for the Flask app in production."""


def get_config(env=None, app: t.Optional['Flask'] = None):
    """Get the configuration for the Flask app."""
    if env is None:
        try:
            env = get_env_variable('NLP4ALL_ENV')
        except EnvironmentError:
            env = 'production'
            print(f'env is not set, using: {env}')
    conf: t.Union[Config, None] = None
    if env == 'production':
        if DB_URI == "":
            raise EnvironmentError('Cannot use SQLite in production')
        conf = ProductionConfig(env)

    if env == 'testing':
        conf = TestConfig(env)

    if env == 'development':
        if DB_URI == "":
            raise EnvironmentError('Cannot use SQLite in production')
        conf = DevelopmentConfig(env)

    if env == 'localdev':
        conf = LocalDevelopmentConfig(env)

    if conf is not None:
        if app is not None:
            conf.DATA_UPLOAD_DIR = os.path.join(app.root_path, conf.DATA_UPLOAD_DIR)
        return conf

    raise EnvironmentError(f'Unknown environment: {env}')
