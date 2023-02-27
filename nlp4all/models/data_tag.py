"""Twee tag model"""  # pylint: disable=invalid-name

from __future__ import annotations

from typing import TYPE_CHECKING
from datetime import datetime

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base

if TYPE_CHECKING:
    from .data_model import DataModel


class DataTagModel(Base):  # pylint: disable=too-few-public-methods
    """DataTag model."""

    __tablename__ = "data_tag"
    id: Mapped[int] = mapped_column(primary_key=True)
    user: Mapped[int] = mapped_column(ForeignKey("user.id"))
    category: Mapped[int] = mapped_column(ForeignKey("data_tag_category.id"))
    analysis: Mapped[int] = mapped_column(ForeignKey("bayesian_analysis.id", ondelete="CASCADE"))
    data_id: Mapped[int] = mapped_column(ForeignKey("nlp_data.id", ondelete="CASCADE"))
    data: Mapped['DataModel'] = relationship(back_populates="tags")
    time_created: Mapped[datetime] = mapped_column(nullable=False, default=datetime.utcnow)
