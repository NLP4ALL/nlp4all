"""User Model""" # pylint: disable=invalid-name

from datetime import datetime, timezone, timedelta
from typing import Union
from flask_login import UserMixin
from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import relationship
import jwt

from .database import Base


class User(Base, UserMixin):
    """User model."""

    __tablename__ = "user"
    id = Column(Integer, primary_key=True)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    image_file = Column(String(20), nullable=False, default="default.jpg")
    password = Column(String(60), nullable=False)
    organizations = relationship(
        "Organization",
        secondary="user_orgs",
        back_populates="users")
    admin = Column(Boolean, default=False)
    roles = relationship("Role", secondary="user_roles")
    analyses = relationship("BayesianAnalysis")
    data_sources = relationship("DataSource")

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

    @staticmethod
    def verify_reset_token(token: str, secret_key: str) -> Union["User", None]:
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
        return User.query.get(user_id)

    def __repr__(self):
        """represents the user object
        without it print(User.query.get(user_id)) returns <user.id>"""
        return f"User('{self.first_name}', '{self.email}', '{self.image_file}')"
