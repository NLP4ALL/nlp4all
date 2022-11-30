"""Helper functions for development."""

from flask import current_app
from flask import jsonify


def help_route():
    """Print available endpoints."""
    func_list = {}
    for rule in current_app.url_map.iter_rules():
        if rule.endpoint != 'static':
            func_list[rule.rule] = current_app.view_functions[rule.endpoint].__doc__
    return jsonify(func_list)
