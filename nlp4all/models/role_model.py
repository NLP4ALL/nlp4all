"""Role model"""  # pylint: disable=invalid-name

import enum
from sqlalchemy import Enum
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base


class Role(enum.Enum):
    """Role."""

    ADMIN = "admin"
    STAFF = "staff"
    STUDENT = "student"


class RoleModel(Base):  # pylint: disable=too-few-public-methods
    """Role model."""

    __tablename__ = "role"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[Role] = mapped_column(Enum(Role), nullable=False, default=Role.STUDENT)
