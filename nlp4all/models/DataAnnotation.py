"""Tweet Annotation model"""  # pylint: disable=invalid-name

from __future__ import annotations

from datetime import datetime
from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .database import Base, MutableJSONB
from . import User, Data

# isn't this just a duplicate of Data (formerly, Tweet)?


class DataAnnotation(Base):  # pylint: disable=too-few-public-methods
    """Data annotation."""

    __tablename__ = "data_annotation"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"))
    user: Mapped[User] = relationship(back_populates="data_annotations")
    # category = Column(Integer, ForeignKey('tweet_tag_category.id'))
    # dropdown: project categories, other
    annotation_tag: Mapped[str] = mapped_column(String(50))
    analysis: Mapped[int] = mapped_column(ForeignKey("bayesian_analysis.id", ondelete="CASCADE"))
    data_id: Mapped[int] = mapped_column(ForeignKey("nlp_data.id", ondelete="CASCADE"))
    data: Mapped[Data] = relationship(back_populates="annotations")
    words: Mapped[dict] = mapped_column(MutableJSONB)
    text: Mapped[str] = mapped_column(String(50))
    coordinates: Mapped[dict] = Column(MutableJSONB)
    time_created: Mapped[datetime] = mapped_column(nullable=False, default=datetime.utcnow)
