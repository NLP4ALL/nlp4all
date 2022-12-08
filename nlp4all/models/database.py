"""SQLAlchemy ORM setup"""

from __future__ import annotations
from sqlalchemy.orm import declarative_base
from flask_sqlalchemy.query import Query
from sqlalchemy_json import mutable_json_type
from sqlalchemy.dialects.postgresql import JSONB


# base model class
class Base: # pylint: disable=too-few-public-methods
    """Base model class"""
    __allow_unmapped__ = True
    query: Query

Base = declarative_base(cls=Base)

NestedMutableJSONB = mutable_json_type(dbtype=JSONB, nested=True)
MutableJSONB = mutable_json_type(dbtype=JSONB, nested=False)

