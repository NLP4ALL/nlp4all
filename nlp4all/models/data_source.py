# pylint: disable=invalid-name
"""DataSource.py: Data source model

This will be use to interface with individual users' data sources
"""

from __future__ import annotations

import typing as t
from sqlalchemy import String
from sqlalchemy.orm import relationship, Mapped, mapped_column

from ..database import Base, NestedMutableJSONB, MutableJSONB, project_data_source_table
from ..helpers.database import schema_aliased_path_dict

if t.TYPE_CHECKING:
    from .data import DataModel
    from .project import ProjectModel


class DataSourceModel(Base):  # pylint: disable=too-few-public-methods
    """DataSource class manages users' data sources"""

    __tablename__ = 'data_source'

    id: Mapped[int] = mapped_column(primary_key=True)
    projects: Mapped[list['ProjectModel']] = relationship(
        secondary=project_data_source_table,
        back_populates="data_sources")
    meta: Mapped[dict] = mapped_column(MutableJSONB, nullable=False)
    schema: Mapped[dict] = mapped_column(NestedMutableJSONB, nullable=False)
    data_source_name: Mapped[str] = mapped_column(String(80), nullable=False)
    data: Mapped[list[DataModel]] = relationship(back_populates="data_source")
    # shared
    # groups / projects /etc need to be implemented

    def _meta_required_keys(self) -> dict[str, object]:
        """Returns a list of required keys for meta

        This is mainly for documentation purposes, but can be used to validate.
        """
        return {
            # this would be how to access the Data.document text property
            # e.g. ('text'), ('user', 'description'), this has to be valid within the schema
            'document_text_path': t.Tuple[str, ...],  # main text of the document used for NLP
            'filterables': t.Dict[str, t.Dict[str, t.Any]],  # Name, Filterable
            'aliased_paths': t.Dict[str, t.Tuple[str, ...]],  # Name, Path: all available data paths
        }

    def _filterable_required_keys(self) -> dict[str, object]:
        """Returns a list of required keys for filterable

        This is mainly for documentation purposes, but can be used to validate.
        """
        return {
            'name': str,
            'type': str,  # FilterableType.value
            'path': t.Tuple[str, ...],  # Used for accessing the value from the document
            'options': t.Dict[str, t.Any]  # See: Filterable
        }

    @property
    def document_text_path(self) -> t.Tuple[str, ...]:
        """Returns the path to the document text"""
        return self.meta['document_text_path']

    @property
    def filterables(self) -> t.Dict[str, t.Dict[str, t.Any]]:
        """Returns the filterables"""
        return self.meta['filterables']

    @property
    def aliased_paths(self) -> t.Dict[str, t.Tuple[str, ...]]:
        """Returns the aliased paths"""
        return self.meta['aliased_paths']

    def aliased_path(self, name: str) -> t.Tuple[str, ...]:
        """Returns the aliased path"""
        return self.meta['aliased_paths'][name]

    def filterable(self, name: str) -> t.Dict[str, t.Any]:
        """Returns the filterable"""
        return self.meta['filterables'][name]

    def path_aliases_from_schema(self) -> dict[str, t.Tuple[str, ...]]:
        """Returns the path aliases from the schema"""
        return schema_aliased_path_dict(self.schema)
