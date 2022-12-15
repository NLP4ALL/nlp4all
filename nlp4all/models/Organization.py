"""Organization model"""  # pylint: disable=invalid-name

from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from ..database import Base, user_org_table


class OrganizationModel(Base):  # pylint: disable=too-few-public-methods
    """Organization model."""

    __tablename__ = "organization"
    id = Column(Integer, primary_key=True)
    name = Column(String(50))
    users = relationship("User", secondary=user_org_table, back_populates="organizations")
    projects = relationship("Project")
