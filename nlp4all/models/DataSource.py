# pylint: disable=invalid-name
"""DataSource.py: Data source model

This will be use to interface with individual users' data sources
"""

from __future__ import annotations

import typing as t
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column

from .database import Base, NestedMutableJSONB, MutableJSONB, project_data_source_table
from . import Data, Project


class DataSource(Base): # pylint: disable=too-few-public-methods
    """DataSource class manages users' data sources"""

    __tablename__ = 'data_source'

    id = Column(Integer, primary_key=True)
    projects: Mapped[list[Project]] = relationship(
        secondary=project_data_source_table,
        back_populates="data_sources")
    meta: Mapped[dict] = mapped_column(MutableJSONB, nullable=False)
    schema: Mapped[dict] = mapped_column(NestedMutableJSONB, nullable=False)
    data_source_name: Mapped[str] = mapped_column(String(80), nullable=False)
    data_id: Mapped[int] = mapped_column(ForeignKey("nlp_data.id"))
    data: Mapped[list[Data]] = relationship(back_populates="data_source")
    # shared
    # groups / projects /etc need to be implemented

    def _meta_required_keys(self) -> dict[str, t.Type]:
        """Returns a list of required keys for meta

        This is mainly for documentation purposes, but can be used to validate.
        """
        return {
            # this would be how to access the Data.document text property
            # e.g. ('text'), ('user', 'description'), this has to be valid within the schema
            'document_text_path': t.Tuple,
            'filterable': t.List[t.Dict]
        }

    def _filterable_required_keys(self) -> dict[str, t.Type]:
        """Returns a list of required keys for filterable

        This is mainly for documentation purposes, but can be used to validate.
        """
        return {
            'name': str,
            'type': str,
            'path': t.Tuple,
            'options': t.List[str]
        }
