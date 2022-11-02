"""Tweet Project model""" # pylint: disable=invalid-name

from sqlalchemy import Column, Integer, ForeignKey

from .database import Base


class TweetProject(Base):  # pylint: disable=too-few-public-methods
    """TweetProject model."""

    __tablename__ = "tweet_project"
    id = Column(Integer(), primary_key=True)
    tweet = Column(Integer(), ForeignKey("tweet.id", ondelete="CASCADE"))
    project = Column(Integer(), ForeignKey("project.id", ondelete="CASCADE"))
