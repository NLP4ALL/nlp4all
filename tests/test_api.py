"""Tests for main nlp4all application API."""

import pytest

from nlp4all import app

# @TODO: this needs refactoring, * import is not needed
from nlp4all.routes import *  # pylint: disable=unused-wildcard-import, wildcard-import


@pytest.mark.api
def test_home():
    """Test home page."""
    tester = app.test_client()
    # check redirect from / to login
    response = tester.get("/")
    assert response.status_code == 200  # pylint: disable=no-member
    assert b"Welcome to NLP4All" in response.data

@pytest.mark.api
def test_login():
    """Test login page."""
    tester = app.test_client()
    # check redirect from /login to login
    response = tester.get("/user/login")
    assert response.status_code == 200  # pylint: disable=no-member
    assert b"Log In" in response.data
