from datetime import datetime

from sqlalchemy import Column, Integer, ForeignKey, DateTime

from .database import Base

class TweetTag(Base): # pylint: disable=too-few-public-methods
    """TweetTag model."""
    id = Column(Integer, primary_key=True)
    user = Column(Integer, ForeignKey("user.id"))
    category = Column(Integer, ForeignKey("tweet_tag_category.id"))
    analysis = Column(Integer, ForeignKey("bayesian_analysis.id", ondelete="CASCADE"))
    tweet = Column(Integer, ForeignKey("tweet.id", ondelete="CASCADE"))
    time_created = Column(DateTime, nullable=False, default=datetime.utcnow)
