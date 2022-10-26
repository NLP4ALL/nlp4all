"""User Orgs model"""

from sqlalchemy import Column, Integer, ForeignKey

from .database import Base

class UserOrgs(Base): # pylint: disable=too-few-public-methods
    """UserOrgs model."""
    __tablename__ = "user_orgs"
    id = Column(Integer(), primary_key=True)
    user_id = Column(Integer(), ForeignKey("user.id", ondelete="CASCADE"))
    role_id = Column(Integer(), ForeignKey("organization.id", ondelete="CASCADE"))