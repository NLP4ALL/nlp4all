"""Role model"""  # pylint: disable=invalid-name

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base


class RoleModel(Base):  # pylint: disable=too-few-public-methods
    """Role model."""

    __tablename__ = "role"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True)
