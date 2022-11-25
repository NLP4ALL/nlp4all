"""Tweet tag category model""" # pylint: disable=invalid-name

from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from .database import Base

class DataTagCategory(Base):  # pylint: disable=too-few-public-methods
    """DataTagCategory model."""

    __tablename__ = "data_tag_category"
    id = Column(Integer, primary_key=True)
    name = Column(String(50))
    description = Column(String(100))
    # data = relationship("Tweet")
    # tags = relationship("DataTag")
    projects = relationship("Project", secondary="project_categories", back_populates="categories")
    # matrices = relationship('ConfusionMatrix', secondary='matrix_categories')

    # @property
    # def data(self):
    #     """Return data"""
    #     return self.
    