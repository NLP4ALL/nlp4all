# make sure we have nginx and dev dependencies
apt-get clean && apt-get -y update
apt-get -y install nginx && apt-get -y install python3-dev && apt-get -y install build-essential

# update pip
python -m pip install --progress-bar off --no-cache-dir --upgrade pip
# install python dependencies
pip install --progress-bar off --no-cache-dir -r requirements.txt

# run gunicorn
gunicorn -w 4 -b 0.0.0.0 'nlp4all:create_app()'