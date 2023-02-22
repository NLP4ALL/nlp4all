# pylint: disable=invalid-name
"""Data.py: Data model

Data imported into nlp4all, used in analyses
"""

from __future__ import annotations

import typing as t
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base, NestedMutableJSONB

if t.TYPE_CHECKING:
    from .data_source import DataSourceModel
    from .data_annotation import DataAnnotationModel
    from .data_tag import DataTagModel
    from .data_tag_category import DataTagCategoryModel


class DataModel(Base):  # pylint: disable=too-few-public-methods
    """Data class for uploaded data"""

    __tablename__ = 'nlp_data'

    _text_path: t.Optional[t.Tuple[str, ...]] = None

    id: Mapped[int] = mapped_column(primary_key=True)
    data_source_id: Mapped[int] = mapped_column(ForeignKey("data_source.id"))
    data_source: Mapped['DataSourceModel'] = relationship(back_populates="data")
    document: Mapped[dict] = mapped_column(NestedMutableJSONB, nullable=False)
    annotations: Mapped[list['DataAnnotationModel']] = relationship(back_populates="data")
    tags: Mapped[list['DataTagModel']] = relationship(back_populates="data")
    category_id: Mapped[int] = mapped_column(ForeignKey("data_tag_category.id"))
    category: Mapped['DataTagCategoryModel'] = relationship(back_populates="data")

    @property
    def text(self) -> str:
        """Returns the text of the document"""
        if self._text_path is None:
            self._text_path = self.data_source.document_text_path
        return self.document[self._text_path]
