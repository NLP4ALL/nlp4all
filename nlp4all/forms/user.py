"""User related forms"""

from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from flask_login import current_user
from wtforms import StringField, SubmitField, PasswordField, BooleanField, SelectField
from wtforms.validators import DataRequired, Length, Email, ValidationError, EqualTo
from nlp4all.models import User


class UpdateAccountForm(FlaskForm):
    """
    Update account form.
    """
    first_name = StringField("First Name", validators=[DataRequired(), Length(min=2, max=20)])
    last_name = StringField("Last Name", validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField("Email", validators=[DataRequired(), Email()])
    picture = FileField("Update Profile Picture", validators=[FileAllowed(["jpg", "png"])])
    submit = SubmitField("Update")


    def validate_email(self, email):
        """
        Validate email.
        """
        if email.data != current_user.email:
            user = User.query.filter_by(email=email.data).first()
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
    first_name = StringField("Name", validators=[DataRequired(), Length(min=2, max=20)])
    last_name = StringField("Last Name", validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    confirm_password = PasswordField(
        "Confirm Password", validators=[DataRequired(), EqualTo("password")]
    )
    organizations = SelectField("Select your organization", validators=[DataRequired()])
    submit = SubmitField("Sign Up")


    def validate_email(self, email):
        """
        Validate email.
        """
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError("That email is taken. Please choose a different one.")


class IMCRegistrationForm(FlaskForm):
    """
    IMC Registration form.
    """

    first_name = StringField("first_name", validators=[DataRequired(), Length(min=2, max=20)])
    submit = SubmitField("Sign Up")


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
        user = User.query.filter_by(email=email.data).first()
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
