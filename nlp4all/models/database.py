"""SQLAlchemy ORM setup"""

import typing as t

from sqlalchemy import Column, ForeignKey, Table
from sqlalchemy.types import TypeEngine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.dialects.postgresql import JSONB, JSON

from sqlalchemy_json import NestedMutable
from flask_sqlalchemy.query import Query


# base model class
class Base(DeclarativeBase):  # pylint: disable=too-few-public-methods
    """Base model class"""
    __allow_unmapped__ = True
    query: Query


# Base: t.Type[N4ABase] = declarative_base(cls=N4ABase)

# Here we define some JSON column types
# we could potentially limit the number
# once we've settled on the final structure
# and the main use of these custom
# classes is to allow us to replace them
# at runtime if we're using sqlite


class N4ANestedJSONB(JSONB):  # pylint: disable=too-many-ancestors
    """Nested JSONB column type"""
    nested = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.impl = JSONB


class N4AFlatJSONB(JSONB):  # pylint: disable=too-many-ancestors
    """Flat JSONB column type"""
    nested = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.impl = JSONB


class N4ANestedJSON(JSON):
    """Nested JSON column type"""
    nested = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.impl = JSON


class N4AFlatJSON(JSON):
    """Nested JSON column type"""
    nested = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.impl = JSON


NestedMutableJSONB: TypeEngine[JSONB] = NestedMutable.as_mutable(N4ANestedJSONB)  # type: ignore
MutableJSONB: TypeEngine[JSONB] = MutableDict.as_mutable(N4AFlatJSONB)  # type: ignore

NestedMutableJSON: t.Type[JSON] = NestedMutable.as_mutable(N4ANestedJSON)  # type: ignore
MutableJSON: TypeEngine[JSON] = MutableDict.as_mutable(N4AFlatJSON)  # type: ignore

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
    Column("data_id", ForeignKey("nlp_data.id", ondelete="CASCADE"), primary_key=True),
    Column("confusion_matrix_id",
           ForeignKey("confusion_matrix.id", ondelete="CASCADE"),
           primary_key=True),
)

matrix_categories_table = Table(
    "matrix_categories",
    Base.metadata,
    Column("data_tag_category_id",
           ForeignKey("data_tag_category.id", ondelete="CASCADE"),
           primary_key=True),
    Column(
        "confusion_matrix_id", ForeignKey("confusion_matrix.id", ondelete="CASCADE"),
        primary_key=True),
)

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
