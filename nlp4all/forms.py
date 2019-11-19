from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from flask_login import current_user
from wtforms import StringField, PasswordField, SubmitField, BooleanField, IntegerField, TextAreaField, SelectMultipleField, SelectField, RadioField, FormField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from nlp4all.models import User, Project 
from wtforms.fields.core import Label


class RegistrationForm(FlaskForm):
    username = StringField('Username',
                           validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password',
                                     validators=[DataRequired(), EqualTo('password')])
    organizations = SelectField('Select your organization', validators=[DataRequired()])
    submit = SubmitField('Sign Up')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('That username is taken. Please choose a different one.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('That email is taken. Please choose a different one.')

class TaggingForm(FlaskForm):
    # choices = RadioField()
    choices = SelectField("Hvem har skrevet dette tweet?")
    submit = SubmitField("Submit")

class TagButton(FlaskForm):
    submit = SubmitField("This doesn't matter apparently")
    
    def set_name(self, new_name):
        self.submit.label = Label("", new_name)

class AddTweetCategoryForm(FlaskForm):
    twitter_handle = StringField('Twitter handle', validators=[DataRequired()])
    submit = SubmitField('Create')


class LoginForm(FlaskForm):
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')


class AddProjectForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    description = StringField('Description', validators=[DataRequired()])
    categories = SelectMultipleField('Categories for your students to work with', validators=[DataRequired()])
    organization = SelectField('Which student group should participate?', validators=[DataRequired()])
    submit = SubmitField("Create Project")

    def validate_title(self, title):
        title = Project.query.filter_by(name=title.data).first()
        if title:
            raise ValidationError('That project name is taken. Please choose a different one.')

class AddBayesianAnalysisForm(FlaskForm):
    name = StringField('Title of Analysis', validators=[DataRequired()])
    shared = BooleanField('Shared project?')
    number = IntegerField("How many of each category?")
    submit = SubmitField('Create Analysis')

class AddBayesianRobotForm(FlaskForm):
    name = StringField('Title of Robot', validators=[DataRequired()])
    submit = SubmitField('Create New Robot')

class AnalysisForm(FlaskForm):
    robort_form = FormField(AddBayesianRobotForm)
    add_category_form = FormField(AddTweetCategoryForm)

class AddBayesianRobotFeatureForm(FlaskForm):
    feature = StringField('Write a word that your robot will look for', validators=[DataRequired()])
    reasoning = StringField("Why do you think that this ")
    submit = SubmitField("Add Word")


class UpdateAccountForm(FlaskForm):
    username = StringField('Username',
                           validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    picture = FileField('Update Profile Picture', validators=[FileAllowed(['jpg', 'png'])])
    submit = SubmitField('Update')

    def validate_username(self, username):
        if username.data != current_user.username:
            user = User.query.filter_by(username=username.data).first()
            if user:
                raise ValidationError('That username is taken. Please choose a different one.')

    def validate_email(self, email):
        if email.data != current_user.email:
            user = User.query.filter_by(email=email.data).first()
            if user:
                raise ValidationError('That email is taken. Please choose a different one.')


class PostForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    content = TextAreaField('Content', validators=[DataRequired()])
    submit = SubmitField('Post')

class AddOrgForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    submit = SubmitField('Add Organization')


class RequestResetForm(FlaskForm):
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    submit = SubmitField('Request Password Reset')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is None:
            raise ValidationError('There is no account with that email. You must register first.')


class ResetPasswordForm(FlaskForm):
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password',
                                     validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Reset Password')
