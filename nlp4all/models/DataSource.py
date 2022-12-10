# pylint: disable=invalid-name
"""DataSource.py: Data source model

This will be use to interface with individual users' data sources
"""

from __future__ import annotations

from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column

from .database import Base, NestedMutableJSONB, project_data_source_table
from . import Data, Project

class DataSource(Base): # pylint: disable=too-few-public-methods
    """DataSource class manages users' data sources"""

    __tablename__ = 'data_source'

    id = Column(Integer, primary_key=True)
    projects: Mapped[list[Project]] = relationship(secondary=project_data_source_table, back_populates="data_sources")    
    structure: Mapped[dict] = mapped_column(NestedMutableJSONB, nullable=False)
    data_source_name: Mapped[str] = mapped_column(String(80), nullable=False)
    data_id: Mapped[int] = mapped_column(ForeignKey("data.id"))
    data: Mapped[list[Data]] = relationship(back_populates="data_source")
    # shared
    # groups / projects /etc need to be implemented
