"""SQLAlchemy ORM setup"""

from sqlalchemy.orm import declarative_base
from flask_sqlalchemy.query import Query

# base model class
class Base: # pylint: disable=too-few-public-methods
    """Base model class"""
    __allow_unmapped__ = True
    query: Query

Base = declarative_base(cls=Base)
