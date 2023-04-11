"""UserGroup model"""  # pylint: disable=invalid-name

import typing as t
from sqlalchemy import String
from sqlalchemy.orm import relationship, Mapped, mapped_column

from ..database import Base, user_org_table, user_group_project_table

if t.TYPE_CHECKING:
    from .user_model import UserModel
    from .project_model import ProjectModel


class UserGroupModel(Base):  # pylint: disable=too-few-public-methods
    """UserGroup model."""

    __tablename__ = "user_group"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    users: Mapped[t.List['UserModel']] = relationship(secondary=user_org_table, back_populates="user_groups")
    projects: Mapped[t.List['ProjectModel']] = relationship(
        secondary=user_group_project_table,
        back_populates="user_groups"
    )
