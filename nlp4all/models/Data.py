# pylint: disable=invalid-name
"""Data.py: Data model

Data imported into nlp4all, used in analyses
"""

from __future__ import annotations

from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy_json import mutable_json_type

from .database import Base, NestedMutableJSONB

class Data(Base): # pylint: disable=too-few-public-methods
    """Data class for uploaded data"""

    __tablename__ = 'data_source'

    id: Mapped[int] = mapped_column(primary_key=True)
    data_source_id: Mapped[int] = mapped_column(ForeignKey("data_source.id"))
    data_source: Mapped["DataSource"] = relationship(back_populates="data")
    text: Mapped[str] = mapped_column(String(255)) # does this need to be longer?
    document: Mapped[dict] = Column(NestedMutableJSONB, nullable=False)
