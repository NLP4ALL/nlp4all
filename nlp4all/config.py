import os
from dotenv import load_dotenv

                                                                         
basedir = os.path.abspath(os.path.dirname(__file__))    
load_dotenv(os.path.join(basedir, '.flaskenv'))                         
load_dotenv(os.path.join(basedir, '.env')) 

class Config(object):
  SQLALCHEMY_TRACK_MODIFICATIONS = False
  SQLALCHEMY_DATABASE_URI = "sqlite:///data/site.db"
