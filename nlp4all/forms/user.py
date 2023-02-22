"""User related forms"""

from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from flask_login import current_user
from wtforms import StringField, SubmitField, PasswordField, BooleanField, SelectField
from wtforms.validators import DataRequired, Length, Email, ValidationError, EqualTo
from ..models import UserModel


class UpdateAccountForm(FlaskForm):
    """
    Update account form.
    """

    username = StringField("Username", validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField("Email", validators=[DataRequired(), Email()])
    picture = FileField("Update Profile Picture", validators=[FileAllowed(["jpg", "png"])])
    submit = SubmitField("Update")

    def validate_username(self, username):
        """
        Validate username.
        """
        if username.data != current_user.username:
            user = UserModel.query.filter_by(username=username.data).first()
            if user:
                raise ValidationError("That username is taken. Please choose a different one.")

    def validate_email(self, email):
        """
        Validate email.
        """
        if email.data != current_user.email:
            user = UserModel.query.filter_by(email=email.data).first()
            if user:
                raise ValidationError("That email is taken. Please choose a different one.")


class LoginForm(FlaskForm):
    """
    Login form.
    """

    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    remember = BooleanField("Remember Me")
    submit = SubmitField("Login")


class RegistrationForm(FlaskForm):
    """
    Registration form.
    """

    username = StringField("Username", validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    confirm_password = PasswordField(
        "Confirm Password", validators=[DataRequired(), EqualTo("password")]
    )
    submit = SubmitField("Sign Up")
    username = StringField("Username", validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    confirm_password = PasswordField(
        "Confirm Password", validators=[DataRequired(), EqualTo("password")]
    )
    organizations = SelectField("Select your organization", validators=[DataRequired()])
    submit = SubmitField("Sign Up")

    def validate_username(self, username):
        """
        Validate username.
        """
        user = UserModel.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError("That username is taken. Please choose a different one.")

    def validate_email(self, email):
        """
        Validate email.
        """
        user = UserModel.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError("That email is taken. Please choose a different one.")


class RequestResetForm(FlaskForm):
    """
    Request reset form.
    """

    email = StringField("Email", validators=[DataRequired(), Email()])
    submit = SubmitField("Request Password Reset")

    def validate_email(self, email):
        """
        Validate email.
        """
        user = UserModel.query.filter_by(email=email.data).first()
        if user is None:
            raise ValidationError("There is no account with that email. You must register first.")


class ResetPasswordForm(FlaskForm):
    """
    Reset password form.
    """

    password = PasswordField("Password", validators=[DataRequired()])
    confirm_password = PasswordField(
        "Confirm Password", validators=[DataRequired(), EqualTo("password")]
    )
    submit = SubmitField("Reset Password")
