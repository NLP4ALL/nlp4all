"""User Roles model""" # pylint: disable=invalid-name

from sqlalchemy import Column, Integer, ForeignKey

from .database import Base


class UserRoles(Base):  # pylint: disable=too-few-public-methods
    """UserRoles model."""

    __tablename__ = "user_roles"
    id = Column(Integer(), primary_key=True)
    user_id = Column(Integer(), ForeignKey("user.id", ondelete="CASCADE"))
    role_id = Column(Integer(), ForeignKey("role.id", ondelete="CASCADE"))
