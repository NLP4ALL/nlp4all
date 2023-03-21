"""Helper functions for development."""

from flask import current_app, jsonify, Response
from ..models import DataSourceModel
from . import data_source
from .. import db


def help_route():
    """Print available endpoints."""
    func_list = {}
    for rule in current_app.url_map.iter_rules():
        if rule.endpoint != 'static':
            func_list[rule.rule] = current_app.view_functions[rule.endpoint].__doc__
    return jsonify(func_list)


def load_data_source(dsid: int) -> Response:
    """Load a data source from the database."""
    ds: DataSourceModel = db.session.query(DataSourceModel).get(dsid)
    paths_to_keep = {'id': ('properties', 'id'), 'url': ('properties', 'url'), 'date': ('properties', 'date'), 'quotedTweet.user.descriptionUrls.url': ('properties', 'quotedTweet', 'properties', 'user', 'properties', 'descriptionUrls', 'items', 'properties', 'url'), 'quotedTweet.user.descriptionUrls.indices': ('properties', 'quotedTweet', 'properties', 'user', 'properties', 'descriptionUrls', 'items', 'properties', 'indices', 'items'), 'content': ('properties', 'content')}
    paths_to_remove = data_source.minimum_paths_for_deletion(paths_to_keep, ds.aliased_paths)
    out = {}

    out['pfs'] = ds.aliased_paths
    out['schema'] = ds.schema
    out['paths_to_remove'] = paths_to_remove
    out['paths_to_keep'] = paths_to_keep
    out['removed'] = data_source.remove_paths_from_schema(ds.schema, paths_to_remove)
    return jsonify(out)
