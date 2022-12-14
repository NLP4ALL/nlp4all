# pylint: disable=invalid-name
"""Data.py: Data model

Data imported into nlp4all, used in analyses
"""

from __future__ import annotations

from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base, NestedMutableJSONB

from . import DataSource, DataAnnotation, DataTag, DataTagCategory


class Data(Base):  # pylint: disable=too-few-public-methods
    """Data class for uploaded data"""

    __tablename__ = 'nlp_data'

    id: Mapped[int] = mapped_column(primary_key=True)
    data_source_id: Mapped[int] = mapped_column(ForeignKey("data_source.id"))
    data_source: Mapped[DataSource] = relationship(back_populates="data")
    text: Mapped[str] = mapped_column(String(500))  # does this need to be longer?
    document: Mapped[dict] = mapped_column(NestedMutableJSONB, nullable=False)
    annotations: Mapped[list[DataAnnotation]] = relationship(back_populates="data")
    tags: Mapped[list[DataTag]] = relationship(back_populates="data")
    category_id: Mapped[int] = mapped_column(ForeignKey("data_tag_category.id"))
    category: Mapped[DataTagCategory] = relationship()
