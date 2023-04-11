"""Helpers for data source manipulation / creation etc"""

from __future__ import annotations

import typing as t
from genson import SchemaBuilder, SchemaNode, SchemaStrategy
from genson.schema.strategies import Object, List, Tuple
from pathlib import Path
import csv
import re


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


def csv_file_to_json(file: Path) -> t.List[dict]:
    """Converts a CSV file to a JSON array.

    Args:
        file: The CSV file to convert.

    Returns:
        The JSON array.

    Raises:
        ValueError: If the CSV is empty.
    """
    with file.open('r') as f:
        csv_data = list(csv.reader(f))
    return csv_to_json(csv_data, None)


def schema_builder() -> N4ASchemaBuilder:
    """Create the schema builder for nlp4all.

    This can be reused to add more data to an existing schema (e.g. on import, for each row).

    Returns:
        The schema builder.
    """
    # add our custom list and object strategies
    N4ASchemaNode.STRATEGIES = tuple([s for s in SchemaBuilder.STRATEGIES if s not in [
        Object, List, Tuple]] + [N4ATuple, N4AList, N4AObject])
    N4ASchemaBuilder.NODE_CLASS = N4ASchemaNode
    N4ASchemaBuilder.STRATEGIES = N4ASchemaNode.STRATEGIES
    return N4ASchemaBuilder()


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
        builder = schema_builder()

    if isinstance(data, list):
        for item in data:
            builder.add_object(item)
    else:
        builder.add_object(data)

    schema = builder.to_schema()

    return schema


def schema_aliased_path_dict(schema: dict,
                             depth: t.Union[None, int] = None,
                             types_only: bool = False) -> t.Dict[str, t.Tuple[str, ...]]:
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
        stype = schema.get("type", [])
        if not isinstance(stype, list):
            stype = [stype]
        if 'object' in stype:
            if "properties" not in schema:
                paths[".".join(new_title_prefix)] = tuple(new_path) if not types_only else tuple(stype)
            else:
                for key, value in schema["properties"].items():
                    new_path = path + ["properties", key]
                    new_title_prefix = title_prefix + [schema["properties"][key].get("title", key)]
                    _schema_aliased_path_dict(
                        value,
                        new_path,
                        new_title_prefix,
                        depth=depth - 1 if depth is not None else None)
        elif 'array' in stype:
            if "items" in schema:
                new_path = path + ["items"]
                for item in schema["items"]:
                    _schema_aliased_path_dict(
                        item,
                        new_path,
                        new_title_prefix,
                        depth=depth - 1 if depth is not None else None)
        elif any(map(lambda v: v in stype, ["string", "number", "integer", "boolean", "null"])):
            paths[".".join(new_title_prefix)] = tuple(new_path) if not types_only else tuple(stype)

    _schema_aliased_path_dict(schema, [], title_prefix=[], depth=depth)

    return paths


def schema_path_to_jsonb_path(path: t.Tuple[str, ...]) -> str:
    """Converts a schema path to a mongodb path.

    This is needed because arrays use [] and objects use . notation.

    example for aliased path "entities.media.sizes.small.h":
        schema_path_to_postgres_path((
                "properties",
                "entities",
                "properties",
                "media",
                "items",
                "properties",
                "sizes",
                "properties",
                "small",
                "properties",
                "h"
            ))
    returns:
        '."entities"."media[*]"."sizes"."small"."h"'


    Args:
        path: The schema path to convert.

    Returns:
        The postgres path.
    """
    postgres_path = []
    for part in path:
        if part == "items":
            postgres_path.append('$[]')
        elif part != "properties":
            postgres_path.append(re.escape(part))
    return ".".join(postgres_path)


def schema_path_index_and_keys_for_pgsql(path: t.Tuple[str, ...]) -> t.List[t.Tuple[int, str]]:
    """Gets the index and key for each part in a schema path.
    This is used in the query because we can't use arrays in the query

    Args:
        path: The schema path to get the index and keys for.

    Returns:
        A list of tuples of the index and key for each part.
    """

    index_and_keys = []
    current_index = 0  # pg is 1 indexed, but the first item is "properties" / root
    for part in path:
        if part == "items":
            current_index += 1
        elif part != "properties":
            current_index += 1
            index_and_keys.append((current_index, part))
    return index_and_keys


def path_with_parents(paths: t.Iterable[str]) -> t.Set[str]:
    """Get a set of all parent paths for the given paths."""

    all_paths: t.List = []
    for path in paths:
        for i in range(1, len(path.split(".")) + 1):
            all_paths += [".".join(path.split(".")[:i])]
    return set(all_paths)


def find_last(lst, sought_elt):
    for r_idx, elt in enumerate(reversed(lst)):
        if elt == sought_elt:
            return len(lst) - 1 - r_idx


def minimum_paths_for_deletion(
        keep: t.Dict[str, t.Tuple[str, ...]],
        paths: t.Dict[str, t.Tuple[str, ...]]) -> t.Dict[str, t.Tuple[str, ...]]:
    """
    Keep only the bare minimum (highest level) items for deletion.
    e.g.
    keep = {
        "a.b.c.d": ("properties", "a", "properties", "b", "items", "properties", "c", "properties", "d"),
        "a.b.c": ("properties", "a", "properties", "b"),
        "x.y": ("properties", "x", "properties", "y")
    }
    paths = {
        "a.b.c.d": ("properties", "a", "properties", "b", "items", "properties", "c", "properties", "d"),
        "a.b.c": ("properties", "a", "properties", "b", "items", "properties", "c"),
        "a.b": ("properties", "a", "properties", "b"),
        "x": ("properties", "x"),
        "x.y": ("properties", "x", "properties", "y"),
        "x.y.z": ("properties", "x", "properties", "y", "properties", "z")
    }
    remove_sub_paths(selected, paths)
    returns:
    {
        "x.y.z": ("properties", "x", "properties", "y", "properties", "z"),
    }
    """
    keep['$schema'] = ('$schema', )
    keep_set = path_with_parents(keep.keys())
    paths_to_remove = {}
    for path, path_tuple in paths.items():
        if path not in keep_set:
            # we only want to add the highest level item
            # if we have a.b.c and a.b, we only want to add a.b
            hierarchy = path.split(".")
            h_len = len(hierarchy)
            if h_len > 1:
                for i in range(1, h_len + 1):
                    parent = ".".join(hierarchy[:i])

                    if parent in paths_to_remove:
                        break
                    if parent in keep_set:
                        continue
                    # the key might not exist if it's an object
                    # because we can't use objects for filtering
                    # but we can use their usable properties
                    if parent in paths:
                        paths_to_remove[parent] = paths[parent]
                    else:
                        # we can use a "pseudo" path, this will be the path_tuple
                        # up to the parent
                        parent_tuple = None
                        for j in range(i, h_len):
                            tmp_path = ".".join(hierarchy[:j])
                            if tmp_path in paths:
                                parent_tuple = paths[tmp_path]
                                break
                        if parent_tuple is None:
                            parent_tuple = path_tuple
                        idx = find_last(parent_tuple, hierarchy[i - 1])
                        if idx is not None:
                            idx += 1
                            paths_to_remove[parent] = parent_tuple[:idx]
                        else:
                            # last resort, just use the whole path
                            paths_to_remove[parent] = parent_tuple
                    break
            else:
                if path_tuple[-1] == "items":
                    paths_to_remove[path] = path_tuple[:-1]
                else:
                    paths_to_remove[path] = path_tuple

    return paths_to_remove

# def build_delete_where_clause()


def nested_get_all(dic: t.Union[t.Dict, t.List[t.Dict]], keys: t.Tuple[str, ...]) -> t.List[t.Any]:
    out = []
    if not isinstance(dic, list):
        dic = [dic]
    n_keys = len(keys)
    for di in dic:
        for i, key in enumerate(keys):
            if isinstance(di, list):
                for d in di:
                    res = nested_get_all(d, keys[i:])
                    if res and not res == []:
                        out += res
            else:
                if key in di:
                    di = di[key]
                    if i == n_keys - 1:
                        out.append(di)
                elif i == n_keys - 1 and "title" in di and di["title"] == key:
                    out.append(di)
    return out


def nested_set(dic: t.Dict, keys: t.Tuple[str, ...], value: t.Any):
    for key in keys[:-1]:
        dic = dic.setdefault(key, {})
    dic[keys[-1]] = value


def nested_set_all(
        dic: t.Union[t.Dict, t.List[t.Dict]],
        keys: t.Tuple[str, ...],
        value: t.Any) -> t.Union[t.Dict, t.List[t.Dict]]:
    is_list = isinstance(dic, list)
    if not is_list:
        dic = [dic]  # type: ignore
    n_keys = len(keys)
    for i, di in enumerate(dic):
        if isinstance(di, list):
            for k, d in enumerate(di):
                res = nested_set_all(d, keys, value)
                di[k] = res
            dic[i] = di  # type: ignore
        else:
            if keys[0] in di:
                if n_keys == 1:
                    di[keys[0]] = value
                    dic[i] = di
                else:
                    dic[i] = nested_set_all(di[keys[0]], keys[1:], value)  # type: ignore
            elif n_keys == 1 and "title" in di and di["title"] == keys[0]:
                di[keys[0]] = value
                dic[i] = di
    if not is_list:
        return dic[0]
    return dic


def nested_del_all(dic: t.Union[t.Dict, t.List[t.Dict]], keys: t.Tuple[str, ...]) -> t.Union[t.Dict, t.List[t.Dict]]:
    is_list = isinstance(dic, list)
    if not is_list:
        dic = [dic]  # type: ignore
    n_keys = len(keys)
    for i, di in enumerate(dic):
        if isinstance(di, list):
            new_list = []
            for k, d in enumerate(di):
                res = nested_del_all(d, keys)
                new_list.append(res)
            dic[i] = new_list  # type: ignore
        else:
            if keys[0] in di:
                if n_keys == 1:
                    del di[keys[0]]
                    dic[i] = di
                else:
                    if n_keys in (2, 3) and "required" in di and keys[-1] in di["required"]:
                        di["required"].remove(keys[-1])
                    new_dict = nested_del_all(di[keys[0]], keys[1:])
                    dic[i] = {**di, keys[0]: new_dict}
            # elif n_keys == 1 and "title" in di and di["title"] == keys[0]:
            #     if "required" in di and keys[-1] in di["required"]:
            #         di["required"].remove(keys[-1])
            #     del dic[i]
            elif n_keys in (2, 3) and "required" in di and keys[-1] in di["required"]:
                di["required"].remove(keys[-1])
                dic[i] = di
    return dic if is_list else dic[0]


def remove_paths_from_schema(schema: t.Dict, paths: t.Dict[str, t.Tuple[str, ...]]) -> dict:
    """Removes the given paths from the schema.

    Args:
        schema: The schema to remove the paths from.
        paths: The paths to remove.

    Returns:
        The schema with the paths removed.
    """

    for path in paths.values():
        try:
            val = []
            val = nested_get_all(schema, path)
            if len(val) == 0:
                continue
            schema = nested_del_all(schema, path)  # type: ignore
        except KeyError:
            continue
        except TypeError:
            pass
    return schema
