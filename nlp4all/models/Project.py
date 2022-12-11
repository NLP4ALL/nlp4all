"""Project Model""" # pylint: disable=invalid-name

from __future__ import annotations

from random import sample
from sqlalchemy import Integer, String, ForeignKey
from sqlalchemy.orm import relationship, load_only, Mapped, mapped_column

from .database import Base, project_data_source_table, project_categories_table, MutableJSON

from . import DataSource, BayesianAnalysis, DataTagCategory, Data


class Project(Base):
    """Project model."""

    __tablename__ = "project"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50))
    description: Mapped[str] = mapped_column()
    organization: Mapped[int] = mapped_column(Integer, ForeignKey("organization.id"))
    analyses: Mapped[list[BayesianAnalysis]] = relationship()
    categories: Mapped[list[DataTagCategory]] = relationship(
        secondary=project_categories_table,
        back_populates="projects")
    data_sources: Mapped[list[DataSource]] = relationship(
        secondary=project_data_source_table,
        back_populates="projects")
    tf_idf: Mapped[dict] = mapped_column(MutableJSON) # what is this?
    # remove? or replace with data?
    # tweets = relationship("Tweet", secondary="tweet_project", lazy="dynamic")
    training_and_test_sets: Mapped[dict] = mapped_column(MutableJSON)

    def get_tweets(self):
        """Get tweets."""
        return [t for cat in self.categories for t in cat.tweets]  # pylint: disable=not-an-iterable

    def get_random_tweet(self):
        """Get a random tweet."""
        tweet_ids = self.tweets.options(load_only("id")).all()  # pylint: disable=no-member
        the_tweet_id = sample(tweet_ids, 1)[0]
        return Data.query.get(the_tweet_id.id)
