"""Twee tag model""" # pylint: disable=invalid-name

from datetime import datetime

from sqlalchemy import Column, Integer, ForeignKey, DateTime

from .database import Base


class DataTag(Base):  # pylint: disable=too-few-public-methods
    """DataTag model."""

    __tablename__ = "data_tag"
    id = Column(Integer, primary_key=True)
    user = Column(Integer, ForeignKey("user.id"))
    category = Column(Integer, ForeignKey("data_tag_category.id"))
    analysis = Column(Integer, ForeignKey("bayesian_analysis.id", ondelete="CASCADE"))
    tweet = Column(Integer, ForeignKey("data.id", ondelete="CASCADE"))
    time_created = Column(DateTime, nullable=False, default=datetime.utcnow)
