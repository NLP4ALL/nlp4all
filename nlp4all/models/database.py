"""SQLAlchemy ORM setup"""

import os
import click
from flask import Flask, current_app, g

# from greenlet import getcurrent
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.ext.declarative import declarative_base

# base model class
Base = declarative_base()

def get_db():
    """Gets the database session.

    Returns:
        scoped_session: The database session.
    """
    if "db" not in g:
        g.db = get_session_from_maker(create_session_maker(current_app.config["SQLALCHEMY_DATABASE_URI"]))
    return g.db

def get_session_from_maker(maker):
    """Gets a session from a sessionmaker.
       and adds the query object to the Base class

    Args:
        maker (sessionmaker): The sessionmaker.

    Returns:
        scoped_session: The database session.
    """

    session = scoped_session(maker)
    Base.query = session.query_property()

    return session

def close_db(exception=None): # pylint: disable=unused-argument
    """Closes the database session at the end of the request."""
    db = g.pop('db', None)

    if db is not None:
        db.remove()

def create_session_maker(conn_string: str) -> sessionmaker:
    """Creates a session for the database.

    Args:
        app (Flask): The Flask app.

    Returns:
        scoped_session: The database session.
    """

    engine = create_engine(
        conn_string,
        pool_pre_ping=True,
        pool_recycle=3600,
        echo=False,
        connect_args={"check_same_thread": False},
    )

    return sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db(): # pylint: disable=too-many-locals
    """Initializes the database."""
    # pylint: disable=import-outside-toplevel, unused-import
    from . import BayesianAnalysis
    from . import BayesianRobot
    from . import ConfusionMatrix
    from . import MatrixCategories
    from . import Organization
    from . import Project
    from . import ProjectCategories
    from . import Role
    from . import Tweet
    from . import TweetAnnotation
    from . import TweetMatrix
    from . import TweetProject
    from . import TweetTag
    from . import TweetTagCategory
    from . import User
    from . import UserOrgs
    from . import UserRoles
    # pylint: enable=wrong-import-position, unused-import
    db = get_db()
    engine = db.get_bind()
    Base.metadata.create_all(bind=engine)

@click.command("init-db")
def init_db_command():
    """Initializes the database."""
    init_db()
    print("Initialized database.")

def drop_db(): # pylint: disable=too-many-locals
    """Drops all tables in the database."""
    # pylint: disable=import-outside-toplevel, unused-import
    from . import BayesianAnalysis
    from . import BayesianRobot
    from . import ConfusionMatrix
    from . import MatrixCategories
    from . import Organization
    from . import Project
    from . import ProjectCategories
    from . import Role
    from . import Tweet
    from . import TweetAnnotation
    from . import TweetMatrix
    from . import TweetProject
    from . import TweetTag
    from . import TweetTagCategory
    from . import User
    from . import UserOrgs
    from . import UserRoles
    # pylint: enable=wrong-import-position, unused-import
    db = get_db()
    engine = db.get_bind()
    Base.metadata.drop_all(bind=engine)

@click.command("drop-db")
def drop_db_command():
    """Drops the database."""
    drop_db()
    print("Dropped database.")

def init_app(app: Flask):
    """Initializes the database for the Flask app.

    Args:
        app (Flask): The Flask app.
    """
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)