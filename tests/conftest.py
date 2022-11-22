"""Pytest fixtures"""
import os
import pytest

os.environ["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
# pylint: disable=import-outside-toplevel

@pytest.fixture
def flask_app():
    """Fixture for app."""
    from nlp4all import app
    return app

@pytest.fixture
def db_session():
    """Fixture for db_session."""
    from nlp4all.models.database import db_session as ds
    return ds

@pytest.fixture
def init_db():
    """Fixture for init_db."""
    from nlp4all.models.database import init_db as idb
    return idb
