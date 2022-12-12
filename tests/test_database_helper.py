"""
Database helper related tests.
"""


import csv, json
from io import StringIO

import pytest

from nlp4all.helpers.database import csv_to_json, generate_schema, csv_row_to_json


@pytest.mark.data
@pytest.mark.helper
def test_csv_row_to_json():
    """Test CSV row to JSON conversion."""
    row = ["a", "b", "c"]
    headers = ["h1", "h2", "h3"]
    json = csv_row_to_json(row, headers)
    assert json == {"h1": "a", "h2": "b", "h3": "c"}


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
    f = StringIO(csvdata)
    csv_reader = csv.reader(f)
    parsed_csv = [row for row in csv_reader]
    json = csv_to_json(parsed_csv, None)

    # make sure there are the same number of rows
    assert len(json) == len(parsed_csv) - 1  # -1 for header

    # make sure that the number of columns is the same
    assert len(json[0]) == len(parsed_csv[1])

    # make sure that the values are the same
    for i in range(len(parsed_csv) - 1):
        # ensure that individual row conversion is correct
        assert json[i] == csv_row_to_json(parsed_csv[i + 1], parsed_csv[0])
        # check each column value
        for j in range(len(parsed_csv[0])):
            assert json[i][parsed_csv[0][j]] == parsed_csv[i + 1][j]


@pytest.mark.data
@pytest.mark.helper
def test_json_schema(jsondata, jsonschema):
    """Test complicated JSON schema generation."""
    parsed_json = json.loads(jsondata)
    schema = generate_schema(parsed_json)

    assert schema == jsonschema
