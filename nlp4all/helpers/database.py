"""Database helpers."""

import typing as t
import click
from genson import SchemaBuilder
from flask import Flask, current_app
from flask.cli import with_appcontext
from nlp4all.models.database import Base


def csv_row_to_json(row: t.List[str], headers: t.List[str]) -> dict:
    """Converts a CSV row to a JSON object.

    Args:
        row: The CSV row to convert.
        headers: The headers for the CSV.

    Returns:
        The JSON object.

    Raises:
        ValueError: If the row and headers are not the same length.
    """
    if len(row) != len(headers):
        raise ValueError("Row and headers are not the same length.")

    return {headers[i]: row[i] for i in range(len(row))}


def csv_to_json(csv: t.List[t.List[str]], headers: t.Union[t.List[str], None]) -> t.List[dict]:
    """Converts a CSV to a JSON array.

    Args:
        csv: The CSV data to convert.
        headers: The headers for the CSV. If None, the first row of the CSV

    Returns:
        The JSON array.

    Raises:
        ValueError: If the CSV is empty.
    """
    if len(csv) == 0:
        raise ValueError("CSV is empty.")

    if headers is None:
        headers = csv[0]
    return [csv_row_to_json(row, headers) for row in csv[1:]]



def generate_schema(
    data: t.Union[dict, t.List[dict]],
    builder: t.Union[SchemaBuilder, None] = None) -> dict:
    """Generates a JSON schema from a (JSON) dictionary or list of (JSON) dictionaries.

    Args:
        data: The data to generate the schema from.
        builder: The SchemaBuilder to use. If None, a new one will be created.
                 Sending a builder allows you to generate add data to an existing
                 schema.

    Returns:
        The generated schema.

    **Note**: If sent a JSON array, the schema will be generated
              based on the _contents_ of the array, not the array itself.

    E.g. Normally if you generate a schema from:
    [{ "a": 1 }, { "b": 2 }] you will get a schema that looks like this:

    {
        "type": "array",
        "items": {
            "type": "object",
            "properties": {
                "a": {
                    "type": "integer"
                },
                "b": {
                    "type": "integer"
                }
            }
        }
    }

    However, if you send the same data to this function,
    you will get a schema that looks like this:

    {
        "type": "object",
        "properties": {
            "a": {
                "type": "integer"
            },
            "b": {
                "type": "integer"
            }
        }
    }

    This is intentional, as this project should save data as
    an item per row, not as an array of items.

    """
    if builder is None:
        builder = SchemaBuilder()

    if isinstance(data, list):
        for item in data:
            builder.add_object(item)
    else:
        builder.add_object(data)

    return builder.to_schema()



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
    