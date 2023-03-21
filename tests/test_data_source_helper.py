"""
Database helper related tests.
"""


import csv
import json
from io import StringIO
import pickle

import pytest

from nlp4all.helpers.data_source import (
    csv_to_json,
    generate_schema,
    csv_row_to_json,
    minimum_paths_for_deletion,
    path_with_parents,
    schema_path_to_jsonb_path,
    schema_path_index_and_keys_for_pgsql,
    remove_paths_from_schema,
    nested_del_all,
    nested_get_all,
    nested_set_all,
    schema_aliased_path_dict
)


@pytest.mark.data
@pytest.mark.helper
def test_csv_row_to_json():
    """Test CSV row to JSON conversion."""
    row = ["a", "b", "c"]
    headers = ["h1", "h2", "h3"]
    json_data = csv_row_to_json(row, headers)
    assert json_data == {"h1": "a", "h2": "b", "h3": "c"}


@pytest.mark.data
@pytest.mark.helper
def test_generate_schema():
    """Test schema generation."""
    data = [
        {"a": 1, "b": 2, "c": 3},
        {"a": 2, "b": 3, "c": 4},
        {"a": 3, "b": 4, "c": 5, "d": 6},
    ]
    schema = generate_schema(data)
    assert schema == {
        "$schema": "http://json-schema.org/schema#",
        "title": "nlp4all",
        "type": "object",
        "properties": {
            "a": {"type": "integer"},
            "b": {"type": "integer"},
            "c": {"type": "integer"},
            "d": {"type": "integer"},
        },
        "required": ["a", "b", "c"],
    }


@pytest.mark.data
@pytest.mark.helper
def test_csv_to_json(csvdata):
    """Test CSV to JSON conversion."""
    fstr = StringIO(csvdata)
    csv_reader = csv.reader(fstr)
    parsed_csv = list(csv_reader)
    json_data = csv_to_json(parsed_csv, None)

    # make sure there are the same number of rows
    assert len(json_data) == len(parsed_csv) - 1  # -1 for header

    # make sure that the number of columns is the same
    assert len(json_data[0]) == len(parsed_csv[1])

    # make sure that the values are the same
    for i in range(len(parsed_csv) - 1):
        # ensure that individual row conversion is correct
        assert json_data[i] == csv_row_to_json(parsed_csv[i + 1], parsed_csv[0])
        # check each column value
        for j in range(len(parsed_csv[0])):
            assert json_data[i][parsed_csv[0][j]] == parsed_csv[i + 1][j]


@pytest.mark.data
@pytest.mark.helper
def test_json_schema(jsondata, jsonschema):
    """Test complicated JSON schema generation."""
    parsed_json = json.loads(jsondata)
    schema = generate_schema(parsed_json)

    assert schema == jsonschema


@pytest.mark.data
@pytest.mark.helper
def test_path_with_parents():
    """Test getting a path with its parents."""
    keep = [
        "a.b",
        "b.a",
    ]

    assert path_with_parents(keep) == set([
        "a",
        "a.b",
        "b",
        "b.a"])


@pytest.mark.data
@pytest.mark.helper
def test_remove_sub_paths():
    """Test removing sub paths from a path dict."""

    keep = {
        "a.b": ("properties", "a", "properties", "a"),
        "b.a": ("properties", "b"),
    }
    paths = {
        "a": ("properties", "a"),
        "a.a": ("properties", "a", "properties", "a"),
        "a.b": ("properties", "a", "properties", "b"),
        "b": ("properties", "b"),
        "b.a": ("properties", "b", "properties", "a"),
        "b.a.a": ("properties", "b", "properties", "a", "properties", "a"),
        "b.a.b": ("properties", "b", "properties", "a", "properties", "b"),
        "b.b": ("properties", "b", "properties", "b"),
        "b.b.a": ("properties", "b", "properties", "b", "properties", "a"),
        "c": ("properties", "c"),
        "c.a": ("properties", "c", "properties", "a"),
        "c.a.a": ("properties", "c", "properties", "a", "properties", "a"),
    }

    paths_to_remove = minimum_paths_for_deletion(keep, paths)
    print(paths_to_remove)
    assert paths_to_remove == {
        "a.a": ("properties", "a", "properties", "a"),
        "b.a.a": ("properties", "b", "properties", "a", "properties", "a"),
        "b.a.b": ("properties", "b", "properties", "a", "properties", "b"),
        "b.b": ("properties", "b", "properties", "b"),
        "c": ("properties", "c"),
    }


@pytest.mark.data
@pytest.mark.helper
def test_schema_path_to_jsonb_path():
    path_tuple = ("properties", "b", "properties", "a", "items", "a")
    assert schema_path_to_jsonb_path(path_tuple) == '$."b"."a"[*]."a"'
    path_tuple = ("properties", "b", "properties", "a", "items", "properties", "a")
    assert schema_path_to_jsonb_path(path_tuple) == '$."b"."a"[*]."a"'


@pytest.mark.data
@pytest.mark.helper
def test_schema_path_index_and_keys_for_pgsql():
    path_tuple = ("properties", "b", "properties", "a", "items", "a")
    assert schema_path_index_and_keys_for_pgsql(path_tuple) == [
        (1, "b"), (2, "a"), (4, "a")]
    path_tuple = ("properties", "b", "properties", "a", "items", "properties", "a")
    assert schema_path_index_and_keys_for_pgsql(path_tuple) == [
        (1, "b"), (2, "a"), (4, "a")]
    path_tuple = ("properties", "b", "properties", "a", "items", "properties", "a", "items", "a")
    assert schema_path_index_and_keys_for_pgsql(path_tuple) == [
        (1, "b"), (2, "a"), (4, "a"), (6, "a")]


@pytest.mark.data
@pytest.mark.helper
def test_remove_paths_from_schema():
    schema = {
        "$schema": "http://json-schema.org/schema#",
        "title": "nlp4all",
        "type": "object",
        "properties": {
            "a": {"type": "integer"},
            "b": {"type": "integer"},
            "c": {"type": "integer"},
            "d": {"type": "integer"},
        },
        "required": ["a", "b", "c"],
    }
    remove = {
        "a": ("properties", "a"),
    }

    # assert remove_paths_from_schema(schema, remove) == {
    #     "$schema": "http://json-schema.org/schema#",
    #     "title": "nlp4all",
    #     "type": "object",
    #     "properties": {
    #         "b": {"type": "integer"},
    #         "c": {"type": "integer"},
    #         "d": {"type": "integer"},
    #     },
    #     "required": ["b", "c"],
    # }


@pytest.mark.data
@pytest.mark.helper
def test_dic_crap():
    schema = json.load(open("tests/data/schema.json"))
    aliased = schema_aliased_path_dict(schema)
    paths_to_keep = {'id': ('properties', 'id'), 'url': ('properties', 'url'), 'date': ('properties', 'date'), 'quotedTweet.user.descriptionUrls.url': ('properties', 'quotedTweet', 'properties', 'user', 'properties', 'descriptionUrls', 'items', 'properties', 'url'), 'quotedTweet.user.descriptionUrls.indices': ('properties', 'quotedTweet', 'properties', 'user', 'properties', 'descriptionUrls', 'items', 'properties', 'indices', 'items'), 'content': ('properties', 'content')}
    paths_to_remove = minimum_paths_for_deletion(paths_to_keep, aliased)

    print("removing paths")
    updated_schema = remove_paths_from_schema(schema, paths_to_remove)
