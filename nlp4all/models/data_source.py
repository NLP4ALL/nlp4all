# pylint: disable=invalid-name
"""DataSource.py: Data source model

This will be use to interface with individual users' data sources
"""

from __future__ import annotations

import typing as t
from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column

from ..database import Base, NestedMutableJSONB, MutableJSONB, project_data_source_table

if t.TYPE_CHECKING:
    from .data import Data
    from .project import Project


class DataSource(Base):  # pylint: disable=too-few-public-methods
    """DataSource class manages users' data sources"""

    __tablename__ = 'data_source'

    id: Mapped[int] = mapped_column(primary_key=True)
    projects: Mapped[list['Project']] = relationship(
        secondary=project_data_source_table,
        back_populates="data_sources")
    meta: Mapped[dict] = mapped_column(MutableJSONB, nullable=False)
    schema: Mapped[dict] = mapped_column(NestedMutableJSONB, nullable=False)
    data_source_name: Mapped[str] = mapped_column(String(80), nullable=False)
    data_id: Mapped[int] = mapped_column(ForeignKey("nlp_data.id"))
    data: Mapped[list[Data]] = relationship(back_populates="data_source")
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
            'filterable': t.Dict[str, t.Dict[str, t.Any]],  # Name, Filterable
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
