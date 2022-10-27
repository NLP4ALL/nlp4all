"""Tweet Annotation model""" # pylint: disable=invalid-name

from datetime import datetime
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, JSON

from .database import Base


class TweetAnnotation(Base):  # pylint: disable=too-few-public-methods
    """Tweet annotation."""

    __tablename__ = "tweet_annotation"
    id = Column(Integer, primary_key=True)
    user = Column(Integer, ForeignKey("user.id"))
    # category = Column(Integer, ForeignKey('tweet_tag_category.id'))
    # dropdown: project categories, other
    annotation_tag = Column(String(50))
    analysis = Column(Integer, ForeignKey("bayesian_analysis.id", ondelete="CASCADE"))
    tweet = Column(Integer, ForeignKey("tweet.id", ondelete="CASCADE"))
    words = Column(JSON)
    text = Column(String(50))
    coordinates = Column(JSON)
    time_created = Column(DateTime, nullable=False, default=datetime.utcnow)
