"""
nlp4all flask app runner.
"""
import importlib
import subprocess
from nlp4all import app
from nlp4all.config import Config


if __name__ == "__main__":
    # ensure required spacy models are installed
    packages = []
    for lang in Config.SPACY_MODEL_LANGUAGES:
        for model_type in Config.SPACY_MODEL_TYPES:
            packages.append(Config.spacy_model_name(lang, model_type))
    for pkg in packages:
        if not importlib.util.find_spec(pkg):
            print(f"Installing required spacy model {pkg}...")
            subprocess.check_call(['python', '-m', 'spacy', 'download', pkg])

    app.run(debug=False)
