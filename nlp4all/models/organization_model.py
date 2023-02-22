"""Organization model"""  # pylint: disable=invalid-name

import typing as t
from sqlalchemy import String
from sqlalchemy.orm import relationship, Mapped, mapped_column

from ..database import Base, user_org_table

if t.TYPE_CHECKING:
    from .user_model import UserModel
    from .project_model import ProjectModel


class OrganizationModel(Base):  # pylint: disable=too-few-public-methods
    """Organization model."""

    __tablename__ = "organization"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50))
    users: Mapped[t.List['UserModel']] = relationship(secondary=user_org_table, back_populates="organizations")
    projects: Mapped[t.List['ProjectModel']] = relationship()
