"""Database helpers."""

import click
from flask import Flask, current_app
from flask.cli import with_appcontext
from nlp4all.models.database import Base


def init_db(): # pylint: disable=too-many-locals
    """Initializes the database."""
    # pylint: disable=import-outside-toplevel, unused-import
    from nlp4all.models import BayesianAnalysis
    from nlp4all.models import BayesianRobot
    from nlp4all.models import ConfusionMatrix
    from nlp4all.models import MatrixCategories
    from nlp4all.models import Organization
    from nlp4all.models import Project
    from nlp4all.models import ProjectCategories
    from nlp4all.models import Role
    from nlp4all.models import Tweet
    from nlp4all.models import TweetAnnotation
    from nlp4all.models import TweetMatrix
    from nlp4all.models import TweetProject
    from nlp4all.models import TweetTag
    from nlp4all.models import TweetTagCategory
    from nlp4all.models import User
    from nlp4all.models import UserOrgs
    from nlp4all.models import UserRoles
    # pylint: enable=wrong-import-position, unused-import
    engine = current_app.extensions["sqlalchemy"].engine
    Base.metadata.create_all(bind=engine)

@click.command("init-db")
@with_appcontext
def init_db_command():
    """Initializes the database."""
    init_db()
    print("Initialized database.")

def drop_db(): # pylint: disable=too-many-locals
    """Drops all tables in the database."""
    # pylint: disable=import-outside-toplevel, unused-import
    from nlp4all.models import BayesianAnalysis
    from nlp4all.models import BayesianRobot
    from nlp4all.models import ConfusionMatrix
    from nlp4all.models import MatrixCategories
    from nlp4all.models import Organization
    from nlp4all.models import Project
    from nlp4all.models import ProjectCategories
    from nlp4all.models import Role
    from nlp4all.models import Tweet
    from nlp4all.models import TweetAnnotation
    from nlp4all.models import TweetMatrix
    from nlp4all.models import TweetProject
    from nlp4all.models import TweetTag
    from nlp4all.models import TweetTagCategory
    from nlp4all.models import User
    from nlp4all.models import UserOrgs
    from nlp4all.models import UserRoles
    # pylint: enable=wrong-import-position, unused-import
    engine = current_app.extensions["sqlalchemy"].get_engine()
    Base.metadata.drop_all(bind=engine)

@click.command("drop-db")
@with_appcontext
def drop_db_command():
    """Drops the database."""
    drop_db()
    print("Dropped database.")

def init_app(app: Flask):
    """Initializes the database for the Flask app.

    Args:
        app (Flask): The Flask app.
    """
    app.cli.add_command(init_db_command)
    app.cli.add_command(drop_db_command)
    