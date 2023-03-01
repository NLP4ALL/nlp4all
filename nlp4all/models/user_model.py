"""User Model"""  # pylint: disable=invalid-name

from __future__ import annotations
import typing as t
from datetime import datetime, timezone, timedelta
from flask_login import UserMixin
from sqlalchemy import Integer, String, Boolean
from sqlalchemy.orm import relationship, Mapped, mapped_column
import jwt

from ..database import Base, user_org_table, user_role_table

if t.TYPE_CHECKING:
    from .user_group import UserGroupModel
    from .role_model import RoleModel
    from .bayesian_analysis import BayesianAnalysisModel
    from .data_annotation import DataAnnotationModel
    from .data_source import DataSourceModel
    from .project_model import ProjectModel


class UserModel(Base, UserMixin):
    """User model."""

    __tablename__ = "user"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    image_file: Mapped[str] = mapped_column(String(20), nullable=False, default="default.jpg")
    password: Mapped[str] = mapped_column(String(60), nullable=False)
    user_groups: Mapped[t.List['UserGroupModel']] = relationship(
        secondary=user_org_table,
        back_populates="users")
    admin: Mapped[bool] = mapped_column(Boolean, default=False)
    roles: Mapped['RoleModel'] = relationship("RoleModel", secondary=user_role_table)
    analyses: Mapped['BayesianAnalysisModel'] = relationship()
    # data_sources: Mapped['DataSourceModel'] = relationship()
    # data_sources should come via project
    data_annotations: Mapped[list['DataAnnotationModel']] = relationship(back_populates="user")
    data_sources: Mapped[list['DataSourceModel']] = relationship(back_populates="user")
    projects: Mapped[list['ProjectModel']] = relationship(back_populates="user")

    def get_reset_token(self, secret_key: str, expires_sec: int = 1800) -> str:
        """Get a reset token.
        Parameters:
            expires_sec (int): Number of seconds the token remains valid
            secret_key (str): Secret key to encode the token
        returns:
            reset_token (str): The token needed to reset the password"""
        reset_token = jwt.encode(
            {
                "user_id": self.id,
                "exp": datetime.now(tz=timezone.utc) + timedelta(seconds=expires_sec),
            },
            secret_key,
            algorithm="HS256",
        )
        return reset_token

    @classmethod
    def verify_reset_token(cls, token: str, secret_key: str) -> t.Union["UserModel", None]:
        """decodes the token
        Parameters:
            token (str): The token needed to reset the password
            secret_key (str): Secret key used to encode the token
        Returns:
            None (None): if the token is invalid
            or
            User.query.get(user_id) ('User') : if the token is valid"""

        try:
            data = jwt.decode(token, secret_key, leeway=timedelta(seconds=10), algorithms=["HS256"])

            user_id = data["user_id"]

        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
        return cls.query.get(user_id)

    def __repr__(self):
        """represents the user object
        without it print(User.query.get(user_id)) returns <user.id>"""
        return f"User('{self.username}', '{self.email}', '{self.image_file}')"


def load_user(user_id):
    """Loads a user from the database.

    Args:
        user_id (int): The id of the user to load.

    Returns:
    User: User object.
    """
    return UserModel.query.get(int(user_id))
