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

project_categories_table = Table(
    "project_categories",
    Base.metadata,
    Column("project_id", ForeignKey("project.id", ondelete="CASCADE"), primary_key=True),
    Column(
        "data_tag_category_id",
        ForeignKey("data_tag_category.id", ondelete="CASCADE"),
        primary_key=True),
)


data_matrices_table = Table(
    "data_matrices",
    Base.metadata,
    Column("data_id", ForeignKey("data.id", ondelete="CASCADE"), primary_key=True),
    Column("confusion_matrix_id",
        ForeignKey("confusion_matrix.id", ondelete="CASCADE"),
        primary_key=True),
)

matrix_categories_table = Table(
    "matrix_categories",
    Base.metadata,
    Column("data_tag_category_id",
    ForeignKey("data_tag_category.id",ondelete="CASCADE"),
    primary_key=True),
    Column(
        "confusion_matrix_id", ForeignKey("confusion_matrix.id", ondelete="CASCADE"),
        primary_key=True),
)

# data_confusionmatrix_table = Table(
#     "tweet_confusionmatrix",
#     Base.metadata,
#     Column("data_id", ForeignKey("data.id", ondelete="CASCADE"), primary_key=True),
#     Column("confusion_matrix_id", ForeignKey("confusion_matrix.id", ondelete="CASCADE"), primary_key=True),
# )

user_role_table = Table(
    "user_roles",
    Base.metadata,
    Column("user_id", ForeignKey("user.id", ondelete="CASCADE"), primary_key=True),
    Column("role_id", ForeignKey("role.id", ondelete="CASCADE"), primary_key=True),
)

user_org_table = Table(
    "user_orgs",
    Base.metadata,
    Column("user_id", ForeignKey("user.id", ondelete="CASCADE"), primary_key=True),
    Column("org_id", ForeignKey("organization.id", ondelete="CASCADE"), primary_key=True),
)
