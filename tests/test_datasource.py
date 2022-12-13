"""Test for datasource models and import flow."""

# import json
# import pytest
# import python_jsonschema_objects as pjs
# from nlp4all.helpers.database import generate_schema


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
