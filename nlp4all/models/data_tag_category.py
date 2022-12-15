"""Tweet tag category model"""  # pylint: disable=invalid-name

from __future__ import annotations

from typing import TYPE_CHECKING
from sqlalchemy import String
from sqlalchemy.orm import relationship, Mapped, mapped_column

from ..database import Base, project_categories_table

if TYPE_CHECKING:
    from .data import Data
    from .data_tag import DataTag
    from .project import Project


class DataTagCategory(Base):  # pylint: disable=too-few-public-methods
    """DataTagCategory model."""

    __tablename__ = "data_tag_category"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50))
    description: Mapped[str] = mapped_column(String(100))
    data: Mapped[list[Data]] = relationship()
    tags: Mapped[list[DataTag]] = relationship()
    projects: Mapped[list[Project]] = relationship(
        secondary=project_categories_table,
        back_populates="categories")
    # matrices = relationship('ConfusionMatrix', secondary='matrix_categories')
