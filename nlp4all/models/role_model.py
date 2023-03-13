"""Role model"""  # pylint: disable=invalid-name

import typing as t
import enum
from sqlalchemy import Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base, user_role_table

if t.TYPE_CHECKING:
    from .user_model import UserModel


class RoleType(enum.Enum):
    """Role."""

    ADMIN = "admin"
    STAFF = "staff"
    STUDENT = "student"


class RoleModel(Base):  # pylint: disable=too-few-public-methods
    """Role model."""

    __tablename__ = "role"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[RoleType] = mapped_column(Enum(RoleType), nullable=False, default=RoleType.STUDENT)
    users: Mapped[t.List['UserModel']] = relationship("UserModel", secondary=user_role_table)
    # user_groups: Mapped[t.List['UserGroupModel']] = relationship("UserGroupModel", back_populates="role")
