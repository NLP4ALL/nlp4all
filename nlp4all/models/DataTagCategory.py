"""Tweet tag category model""" # pylint: disable=invalid-name

from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship, Mapped, mapped_column

from .database import Base
from . import Data, DataTag, Project


class DataTagCategory(Base):  # pylint: disable=too-few-public-methods
    """DataTagCategory model."""

    __tablename__ = "data_tag_category"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50))
    description: Mapped[str] = mapped_column(String(100))
    tweets: Mapped[list[Data]] = relationship()
    tags: Mapped[list[DataTag]] = relationship()
    projects: Mapped[list[Project]] = relationship(secondary="project_categories", back_populates="categories")
    # matrices = relationship('ConfusionMatrix', secondary='matrix_categories')
