"""
nlp4all flask app runner.
"""
from flask import jsonify
from nlp4all import app

@app.route('/api/help', methods = ['GET'])
def help_route():
    """Print available functions."""
    func_list = {}
    for rule in app.url_map.iter_rules():
        if rule.endpoint != 'static':
            func_list[rule.rule] = app.view_functions[rule.endpoint].__doc__
    return jsonify(func_list)

if __name__ == "__main__":
    app.run(debug=True)
