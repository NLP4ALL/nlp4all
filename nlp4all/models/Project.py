"""Project Model""" # pylint: disable=invalid-name

from random import sample
from sqlalchemy import Column, Integer, String, ForeignKey, JSON
from sqlalchemy.orm import relationship, load_only, Mapped, mapped_column

from .database import Base, project_data_source_table

from . import Tweet, DataSource, BayesianAnalysis, DataTagCategory


class Project(Base):
    """Project model."""

    __tablename__ = "project"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50))
    description: Mapped[str] = mapped_column()
    organization: Mapped[int] = mapped_column(Integer, ForeignKey("organization.id"))
    analyses: Mapped[list[BayesianAnalysis]] = relationship()
    categories: Mapped[list[DataTagCategory]] = relationship(
        secondary="project_categories",
        back_populates="projects")
    data_sources: Mapped[list[DataSource]] = relationship(secondary=project_data_source_table, back_populates="projects")
    tf_idf: Mapped[dict] = mapped_column(JSON) # what is this?
    tweets = relationship("Tweet", secondary="tweet_project", lazy="dynamic") # remove? or replace with data?
    training_and_test_sets: Mapped[dict] = mapped_column(JSON)

    def get_tweets(self):
        """Get tweets."""
        return [t for cat in self.categories for t in cat.tweets]  # pylint: disable=not-an-iterable

    def get_random_tweet(self):
        """Get a random tweet."""
        tweet_ids = self.tweets.options(load_only("id")).all()  # pylint: disable=no-member
        the_tweet_id = sample(tweet_ids, 1)[0]
        return Tweet.query.get(the_tweet_id.id)
