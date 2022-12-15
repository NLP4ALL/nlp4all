"""Role model"""  # pylint: disable=invalid-name

from sqlalchemy import Column, Integer, String

from ..database import Base


class Role(Base):  # pylint: disable=too-few-public-methods
    """Role model."""

    __tablename__ = "role"
    id = Column(Integer(), primary_key=True)
    name = Column(String(50), unique=True)
