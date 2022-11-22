"""ProjectCategories model""" # pylint: disable=invalid-name

from sqlalchemy import Column, Integer, ForeignKey

from .database import Base


class ProjectCategories(Base):  # pylint: disable=too-few-public-methods
    """ProjectCategories model."""

    __tablename__ = "project_categories"
    id = Column(Integer(), primary_key=True)
    project_id = Column(Integer(), ForeignKey("project.id", ondelete="CASCADE"))
    category_id = Column(Integer(), ForeignKey("tweet_tag_category.id", ondelete="CASCADE"))
