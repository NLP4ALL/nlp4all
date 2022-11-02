"""Project Model""" # pylint: disable=invalid-name

from random import sample
from sqlalchemy import Column, Integer, String, ForeignKey, JSON
from sqlalchemy.orm import relationship, load_only

from .database import Base
from . import Tweet


class Project(Base):
    """Project model."""

    __tablename__ = "project"
    id = Column(Integer, primary_key=True)
    name = Column(String(50))
    description = Column(String)
    organization = Column(Integer, ForeignKey("organization.id"))
    analyses = relationship("BayesianAnalysis")
    categories = relationship("TweetTagCategory", secondary="project_categories")
    tf_idf = Column(JSON)
    tweets = relationship("Tweet", secondary="tweet_project", lazy="dynamic")
    training_and_test_sets = Column(JSON)

    def get_tweets(self):
        """Get tweets."""
        return [t for cat in self.categories for t in cat.tweets]  # pylint: disable=not-an-iterable

    def get_random_tweet(self):
        """Get a random tweet."""
        tweet_ids = self.tweets.options(load_only("id")).all()  # pylint: disable=no-member
        the_tweet_id = sample(tweet_ids, 1)[0]
        return Tweet.query.get(the_tweet_id.id)
