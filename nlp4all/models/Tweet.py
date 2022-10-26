"""Tweet model"""

from sqlalchemy import Column, Integer, String, ForeignKey, JSON, DateTime
from sqlalchemy.orm import relationship

from .database import Base

class Tweet(Base): # pylint: disable=too-few-public-methods
    """Tweet model."""
    __tablename__ = "tweet"
    id = Column(Integer, primary_key=True)
    time_posted = Column(DateTime)
    category = Column(Integer, ForeignKey("tweet_tag_category.id"))
    projects = Column(Integer, ForeignKey("project.id"))
    handle = Column(String(15))
    full_text = Column(String(280))
    words = Column(JSON)
    hashtags = Column(JSON)
    tags = relationship("TweetTag")
    links = Column(JSON)
    mentions = Column(JSON)
    url = Column(String(200), unique=True)
    text = Column(String(300))
    annotations = relationship("TweetAnnotation")