# pylint: disable=invalid-name
"""DataSource.py: Data source model

This will be use to interface with individual users' data sources
"""

from __future__ import annotations

from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship, Mapped
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy_json import NestedMutableJson, mutable_json_type

from .database import Base

class DataSource(Base): # pylint: disable=too-few-public-methods
    """DataSource class manages users' data sources"""

    __tablename__ = 'data_source'

    id = Column(Integer, primary_key=True)
    user = Column(Integer, ForeignKey("user.id"), nullable=False)
    structure: Mapped[dict] = Column(NestedMutableJson, nullable=False)
    data_source_name = Column(String(80), nullable=False)
    data: Mapped[list["Data"]] = relationship(back_populates="data_source")
    # shared
    # groups / projects /etc need to be implemented
