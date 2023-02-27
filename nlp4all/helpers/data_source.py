"""Helpers for data source manipulation / creation etc"""

from __future__ import annotations

import typing as t
from genson import SchemaBuilder, SchemaNode, SchemaStrategy
from genson.schema.strategies import Object, List, Tuple


class N4AObject(Object):
    """JSON Object strategy for nlp4all."""

    current_key: t.Optional[str] = None

    def to_schema(self):
        """Converts the strategy to a schema."""

        schema = super().to_schema()
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

    current_key: t.Optional[str] = None

    def items_to_schema(self):
        """Overrides the super class method to add current_key"""
        self._items.current_key = self.current_key
        return self._items.to_schema()


class N4ATuple(Tuple):
    """Tuple strategy for nlp4all."""

    current_key: t.Optional[str] = None

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

    STRATEGIES: t.Optional[t.Tuple[t.Type[SchemaStrategy], ...]] = None
    current_key: t.Optional[str] = None

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
    NODE_CLASS: t.Optional[t.Type[SchemaNode]] = None
    STRATEGIES: t.Optional[t.Tuple[t.Type[SchemaStrategy], ...]] = None

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

              Additionally, any null schemas will be removed, and if there
              are cases of anyOf types with "null" and another type, the
              "null" will be removed, and the other type will be used as
              the schema.

              Finally, this also applies to empty arrays, they will be removed.

    E.g. Normally if you generate a schema from a top level json array:
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
        N4ASchemaNode.STRATEGIES = tuple([s for s in SchemaBuilder.STRATEGIES if s not in [
                                         Object, List, Tuple]] + [N4ATuple, N4AList, N4AObject])
        N4ASchemaBuilder.NODE_CLASS = N4ASchemaNode
        N4ASchemaBuilder.STRATEGIES = N4ASchemaNode.STRATEGIES
        builder = N4ASchemaBuilder()

    if isinstance(data, list):
        for item in data:
            builder.add_object(item)
    else:
        builder.add_object(data)

    schema = builder.to_schema()

    return schema


def schema_aliased_path_dict(schema: dict,
                             depth: t.Union[None, int] = None) -> t.Dict[str, t.Tuple[str, ...]]:
    """Gets a dictionary of all paths in a schema, with their aliases.
    This recursively goes through a json schema and returns a list of paths to
    all properties that can contain data (i.e. not objects or arrays).

    Aliases are the contents of the "title" field of a schema.

    Args:
        schema: The schema to get the paths from.
        depth: The depth to go to. If None, will go to the end.

    Returns:
        A dictionary of paths to aliases. The format is:
        {
            "namespaced.field.alias": ("full", "path", "to", "field"),
            ...
        }
    """
    paths = {}

    def _schema_aliased_path_dict(
            schema: dict,
            path: t.List[str],
            title_prefix: t.List[str],
            depth: t.Union[None, int] = None):
        """Recursive function to get the paths."""
        if depth is not None and depth <= 0:
            return

        new_path = path
        new_title_prefix = title_prefix

        if "properties" in schema:
            for key, value in schema["properties"].items():
                new_path = path + [key]
                new_title_prefix = title_prefix + [schema["properties"][key].get("title", key)]
                _schema_aliased_path_dict(
                    value,
                    new_path,
                    new_title_prefix,
                    depth=depth - 1 if depth is not None else None)
        elif "items" in schema:
            new_path = path + ["items"]
            new_title_prefix = title_prefix + [schema.get("title", "items")]
            _schema_aliased_path_dict(schema["items"], new_path, new_title_prefix,
                                      depth=depth - 1 if depth is not None else None)

        paths[".".join(new_title_prefix)] = tuple(new_path)

    _schema_aliased_path_dict(schema, [], title_prefix=[], depth=depth)

    return paths