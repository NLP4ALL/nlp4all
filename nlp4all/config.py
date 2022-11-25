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
    SQLALCHEMY_DATABASE_URI = "sqlite:///data/site.db"
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
