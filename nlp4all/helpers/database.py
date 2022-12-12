"""Database helpers."""

import typing as t
import click
from genson import SchemaBuilder, SchemaNode
from genson.schema.strategies import Object, List, Tuple
from flask import Flask, current_app
from flask.cli import with_appcontext
from nlp4all.models.database import Base

class N4AObject(Object):
    """JSON Object strategy for nlp4all."""

    current_key = None

    def to_schema(self):
        """Converts the strategy to a schema."""

        schema =  super().to_schema()
        if self.current_key is not None:
            schema['title'] = self.current_key
        return schema

    def _properties_to_schema(self, properties):
        """Overrides the super class method to add current_key"""
        schema_properties = {}
        for prop, schema_node in properties.items():
            schema_node.current_key = prop
            schema = schema_node.to_schema()

            # remove empty objects
            try:
                items = schema['items']
                if items is None:
                    if self._required is not None:
                        self._required.remove(prop)
                    continue
                if len(items) == 1 and items[0] == {}:
                    if self._required is not None:
                        self._required.remove(prop)
                    continue
            except KeyError:
                pass

            # remove null types
            try:
                stype = schema['type']
                if stype == 'null':
                    if self._required is not None:
                        self._required.remove(prop)
                    continue
            except KeyError:
                pass
            schema_properties[prop] = schema
        return schema_properties

class N4AList(List):
    """List strategy for nlp4all.
    """

    current_key = None

    def items_to_schema(self):
        """Overrides the super class method to add current_key"""
        self._items.current_key = self.current_key
        return self._items.to_schema()

class N4ATuple(Tuple):
    """Tuple strategy for nlp4all."""

    current_key = None

    def items_to_schema(self):
        """Overrides the super class method to add current_key"""
        for item in self._items:
            item.current_key = self.current_key
        return [item.to_schema() for item in self._items]

    # def items_to_schema(self):
    #     schema = []
    #     for item in self._items:
    #         item.current_key = self.current_key
    #         schema.append(item.to_schema())
    #     return schema

class N4ASchemaNode(SchemaNode):
    """Schema node for nlp4all."""

    STRATEGIES = None
    current_key = None

    def to_schema(self):
        """Converts the node to a schema.
        This is a modified version of the original to_schema method
        in order to remove the anyOf field from the schema.
        Icky, but in the specific case of two types, "null" and <something else>,
        the anyOf field is not needed, as we treat pretty much everything as optional.
        """

        if self.current_key is not None:
            for active_strategy in self._active_strategies:
                if isinstance(active_strategy, (N4AObject, N4AList, N4ATuple)):
                    active_strategy.current_key = self.current_key

        schema = super().to_schema()
        try:
            types = schema['anyOf']
            if types is None:
                return schema
            if len(types) == 2:
                if types[0]['type'] == 'null':
                    return types[1]
                if types[1]['type'] == 'null':
                    return types[0]
        except KeyError:
            pass

        return schema

class N4ASchemaBuilder(SchemaBuilder):
    """Schema builder for nlp4all."""

    # set to none, assigning here doesn't work
    NODE_CLASS = None
    STRATEGIES = None

    def to_schema(self):
        """Overrides the default to_schema method to
        add a top level title field.
        """
        schema = super().to_schema()
        schema['title'] = 'nlp4all'
        return schema




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
        raise ValueError(
            f"Row and headers are not the same length. Row: {row}, Headers: {headers}")

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
        csv = csv[1:]
    return [csv_row_to_json(row, headers) for row in csv]



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
        # add our custom list and object strategies
        N4ASchemaNode.STRATEGIES = tuple([s for s in SchemaBuilder.STRATEGIES if s not in [Object, List, Tuple]] + [N4ATuple, N4AList, N4AObject]) # pylint: disable=line-too-long
        N4ASchemaBuilder.NODE_CLASS = N4ASchemaNode
        N4ASchemaBuilder.STRATEGIES = N4ASchemaNode.STRATEGIES
        builder = N4ASchemaBuilder()

    if isinstance(data, list):
        for item in data:
            builder.add_object(item)
    else:
        builder.add_object(data)

    schema = builder.to_schema()
    # Mapping for "$id" to "$schema" for compatibility with
    # python_jsonschema_objects
    # schema["$id"] = schema["$schema"]
    return schema



def init_db(): # pylint: disable=too-many-locals
    """Initializes the database."""
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


def model_cols_jsonb_to_json(app: Flask, cls: type): # pylint: disable=too-many-locals
    """Converts a Postgres JSONB column to a SQLite JSON column.
    Within the model itself, the column is defined as a JSONB column,
    we only need to change this to JSON when we are using SQLite.

    Currently only Data and DataSource use JSONB, and we only need to
    change these when we're testing, or local dev (which both use sqlite).
    """
    # pylint: disable=import-outside-toplevel, unused-import
    from sqlalchemy.dialects.sqlite import JSON
    from sqlalchemy_json import mutable_json_type, NestedMutable
    from sqlalchemy.ext.mutable import MutableDict
    from nlp4all.models.database import N4AFlatJSON, N4ANestedJSON, N4AFlatJSONB, N4ANestedJSONB

    SQLiteNestedMutableJSON = mutable_json_type(dbtype=JSON, nested=True) # pylint: disable=invalid-name
    SQLiteMutableJSON = mutable_json_type(dbtype=JSON, nested=False) # pylint: disable=invalid-name

    tables = cls.__subclasses__()
    for tbl in tables:
        type_changed = False
        app.logger.warning(">>> Converting table [%s] to SQLite JSON ===", tbl.__tablename__)
        for col in tbl.__table__.columns:
            if isinstance(col.type, (N4ANestedJSON, N4ANestedJSONB)):
                app.logger.warning("      Converting column [%s] from %s to %s (DBTYPE: %s)",
                    col.name,
                    type(col.type),
                    NestedMutable,
                    JSON)
                col.type = SQLiteNestedMutableJSON
                type_changed = True
                continue
            if isinstance(col.type, (N4AFlatJSON, N4AFlatJSONB)):
                app.logger.warning("      Converting column [%s] from %s to %s (DBTYPE: %s)",
                    col.name,
                    type(col.type),
                    MutableDict,
                    JSON)
                col.type = SQLiteMutableJSON
                type_changed = True
                continue
        if type_changed:
            app.logger.warning(
                "+++ Done converting table [%s] to SQLite JSON +++\n",
                tbl.__tablename__)
        else:
            app.logger.warning(
                "--- No changes to table [%s] ---\n",
                tbl.__tablename__)
    # pylint: enable=import-outside-toplevel, unused-import
