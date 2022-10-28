"""Tweet Matrix model""" # pylint: disable=invalid-name

from sqlalchemy import Column, Integer, ForeignKey

from .database import Base


class TweetMatrix(Base):  # pylint: disable=too-few-public-methods
    """TweetMatrix model."""

    __tablename__ = "tweet_confusionmatrix"
    id = Column(Integer(), primary_key=True)
    tweet = Column(Integer(), ForeignKey("tweet.id", ondelete="CASCADE"))
    matrix = Column(Integer(), ForeignKey("confusion_matrix.id", ondelete="CASCADE"))
