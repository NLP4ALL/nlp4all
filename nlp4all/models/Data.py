# pylint: disable=invalid-name
"""Data.py: Data model

Data imported into nlp4all, used in analyses
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base, NestedMutableJSONB

if TYPE_CHECKING:
    from .data_source import DataSourceModel
    from .data_annotation import DataAnnotationModel
    from .data_tag import DataTagModel
    from .data_tag_category import DataTagCategoryModel


class DataModel(Base):  # pylint: disable=too-few-public-methods
    """Data class for uploaded data"""

    __tablename__ = 'nlp_data'

    id: Mapped[int] = mapped_column(primary_key=True)
    data_source_id: Mapped[int] = mapped_column(ForeignKey("data_source.id"))
    data_source: Mapped[DataSourceModel] = relationship(back_populates="data")
    text: Mapped[str] = mapped_column(String(500))  # does this need to be longer?
    document: Mapped[dict] = mapped_column(NestedMutableJSONB, nullable=False)
    annotations: Mapped[list[DataAnnotationModel]] = relationship(back_populates="data")
    tags: Mapped[list[DataTagModel]] = relationship(back_populates="data")
    category_id: Mapped[int] = mapped_column(ForeignKey("data_tag_category.id"))
    category: Mapped[DataTagCategoryModel] = relationship()
