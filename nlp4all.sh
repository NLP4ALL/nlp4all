gunicorn -w 8 --threads 8  -b 127.0.0.1:5000 nlp4all:app
