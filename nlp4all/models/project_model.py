"""Project Model"""  # pylint: disable=invalid-name

from __future__ import annotations

import enum
import typing as t
# from random import sample
from sqlalchemy import Integer, String, ForeignKey, Enum
from sqlalchemy.orm import relationship, Mapped, mapped_column

from ..database import Base, project_data_source_table, project_categories_table, MutableJSON, user_group_project_table

if t.TYPE_CHECKING:
    from .data_source import DataSourceModel
    from .bayesian_analysis import BayesianAnalysisModel
    from .data_tag_category import DataTagCategoryModel
    from .user_model import UserModel
    from .user_group import UserGroupModel


class ProjectStatus(enum.Enum):
    """Project status."""

    ACTIVE = "active"
    DRAFT = "draft"
    DELETED = "deleted"


class ProjectModel(Base):
    """Project model."""

    __tablename__ = "project"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50))
    description: Mapped[str] = mapped_column()
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("user.id"))
    user: Mapped[UserModel] = relationship(back_populates="projects")
    user_groups: Mapped[list[UserGroupModel]] = relationship(
        secondary=user_group_project_table,
        back_populates="projects")
    analyses: Mapped[list['BayesianAnalysisModel']] = relationship(back_populates="project")
    categories: Mapped[list['DataTagCategoryModel']] = relationship(
        secondary=project_categories_table,
        back_populates="projects")
    data_sources: Mapped[list['DataSourceModel']] = relationship(
        secondary=project_data_source_table,
        back_populates="projects")
    tf_idf: Mapped[dict] = mapped_column(MutableJSON)  # what is this?
    # remove? or replace with data?
    # tweets = relationship("Tweet", secondary="tweet_project", lazy="dynamic")

    training_and_test_sets: Mapped[dict] = mapped_column(MutableJSON)
    status: Mapped[ProjectStatus] = mapped_column(
        Enum(ProjectStatus),
        default=ProjectStatus.DRAFT.value,
        nullable=False)

    def get_tweets(self):
        """Get tweets."""
        return [t for cat in self.categories for t in cat.data]  # pylint: disable=not-an-iterable

    # def get_random_tweet(self):
    #     """Get a random tweet."""
    #     tweet_ids = self.data.options(load_only("id")).all()  # pylint: disable=no-member
    #     the_tweet_id = sample(tweet_ids, 1)[0]
    #     return Data.query.get(the_tweet_id.id)
