"""SQLAlchemy ORM setup"""

from __future__ import annotations
from sqlalchemy import Column, ForeignKey, Table
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

# Definitions for many-to-many relationships

project_data_source_table = Table(
    "project_data_source",
    Base.metadata,
    Column("project_id", ForeignKey("project.id"), primary_key=True),
    Column("data_source_id", ForeignKey("data_source.id"), primary_key=True),
)


data_tag_category = Table()

tweet_project = Table()

user_role = Table()

user_org = Table()