"""Organization model""" # pylint: disable=invalid-name

from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from .database import Base


class Organization(Base):  # pylint: disable=too-few-public-methods
    """Organization model."""

    __tablename__ = "organization"
    id = Column(Integer, primary_key=True)
    name = Column(String(50))
    users = relationship("User", secondary="user_orgs")
    projects = relationship("Project")