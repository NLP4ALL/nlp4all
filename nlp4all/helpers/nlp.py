"""NLP helpers, a mess at the moment"""

import importlib
import subprocess
import click
from flask import current_app
from flask.cli import with_appcontext

from nlp4all.config import Config


def clean_word(aword):
    """remove twitter handles, hashtags, and urls

    Args:
        aword (str): the word to clean

    Returns:
        _type_: the unmodified word, or a generic word if the word was a handle, hashtag, or url
    """
    if "@" in aword:
        return "@twitter_ID"
    if "#" in aword:
        return "#hashtag"
    if "http" in aword:
        return "http://link"
    return aword


def remove_hash_links_mentions(text):
    """remove hashtags, links, and mentions from a tweet"""
    text = [w for w in text.lower().split() if "#" not in w and "http" not in w and "@" not in w]
    text = " ".join(text)
    return text


def clean_non_transparencynum(text):
    """remove non-transparencynum characters from a string"""
    text = text.replace(".", " ")
    text = text.replace("!", " ")
    text = text.replace("”", " ")
    text = text.replace('"', " ")
    text = text.replace("'", " ")
    text = text.replace("“", " ")
    text = text.replace("?", " ")
    text = text.replace(":", " ")
    text = text.replace("'", " ")
    text = text.replace("-", " ")
    text = text.replace("/", " ")
    text = text.replace("-", " ")
    text = text.replace("–", " ")
    text = text.replace(",", " ")
    text = text.replace("(", " ")
    text = text.replace(")", " ")
    return text.strip()  # changed this, might not work!


@click.command("spacy-download")
@with_appcontext
def get_spacy_models():
    """Download the spacy models"""
    current_app.config.get("SPACY_MODEL_LANGUAGES")
    packages = []
    for lang in current_app.config.get("SPACY_MODEL_LANGUAGES"):
        for model_type in current_app.config.get("SPACY_MODEL_TYPES"):
            packages.append(Config.spacy_model_name(lang, model_type))
    for pkg in packages:
        if not importlib.util.find_spec(pkg):
            print(f"Installing required spacy model {pkg}...")
            subprocess.check_call(['python', '-m', 'spacy', 'download', pkg])


def init_app(app):
    """Initialize the app with the spacy download command"""
    app.cli.add_command(get_spacy_models)
