"""Test for datasource models and import flow."""

# import json
# import pytest
# import python_jsonschema_objects as pjs
from nlp4all.helpers.data_source import schema_aliased_path_dict


def test_schema_to_path_dict(jsonschema, schema_paths):
    """Test schema to path dict."""
    schema = {
        "type": "object",
        "properties": {
            "user": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "age": {"type": "number"},
                },
            },
            "text": {"type": "string"},
        },
    }

    paths = {
        "user.name": ("user", "name"),
        "user.age": ("user", "age"),
        "text": ("text",),
    }

    # simple example
    assert schema_aliased_path_dict(schema) == paths

    # complex example
    assert schema_aliased_path_dict(jsonschema) == schema_paths

# @pytest.mark.data
# # @pytest.mark.model
# def test_data_import_csv(app, csvdata):
#     """Test data import from CSV."""
#     from nlp4all.models import DataSource
#     # from nlp4all.helpers.datasets import csv_to_json

#     ds = DataSource()


#     ds.delete()


# @pytest.mark.data
# @pytest.mark.model
# def test_data_import_json(jsondata):
#     """Test data import from JSON."""
#     parsed_json = json.loads(jsondata)
#     schema = generate_schema(parsed_json)
#     builder = pjs.ObjectBuilder(schema)
#     classes = builder.build_classes(named_only=True)
#     cln = [str(x) for x in dir(classes)]
#     tst = classes.Nlp4all()
#     k = ns.keys()
#     v = ns.items()
#     assert len(ns) == 1
