"""
nlp4all flask app runner.
"""
from nlp4all import app
from nlp4all.routes import *

if __name__ == "__main__":
    app.run(debug=True)
