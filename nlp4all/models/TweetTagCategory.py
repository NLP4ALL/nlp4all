from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from .database import Base

class TweetTagCategory(Base): # pylint: disable=too-few-public-methods
    """TweetTagCategory model."""
    id = Column(Integer, primary_key=True)
    name = Column(String(50))
    description = Column(String(100))
    tweets = relationship("Tweet")
    tags = relationship("TweetTag")
    projects = relationship("Project", secondary="project_categories")
    # matrices = relationship('ConfusionMatrix', secondary='matrix_categories')