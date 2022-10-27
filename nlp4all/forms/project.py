"""Project forms"""

from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from flask_login import current_user
from wtforms import (
    StringField,
    SubmitField,
    PasswordField,
    BooleanField,
    SelectField
)
from wtforms.validators import DataRequired, Length, Email, ValidationError, EqualTo
from nlp4all.models import User

