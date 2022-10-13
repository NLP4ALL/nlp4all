"""
nlp4all flask app runner.
"""
from nlp4all import app
# @TODO: this needs refactoring, * import is not needed
from nlp4all.routes import *  # pylint: disable=unused-wildcard-import, wildcard-import

if __name__ == "__main__":
    app.run(debug=True)
