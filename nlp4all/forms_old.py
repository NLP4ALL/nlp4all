"""
Flask forms.
"""
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from flask_login import current_user
from wtforms import (
    StringField,
    PasswordField,
    SubmitField,
    BooleanField,
    IntegerField,
    TextAreaField,
    SelectMultipleField,
    SelectField,
    FormField,
    FloatField,
    HiddenField,
)
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from wtforms.fields.core import Label
from nlp4all.models import User, Project



class IMCRegistrationForm(FlaskForm):
    """
    IMC Registration form.
    """
    username = StringField("Username", validators=[DataRequired(), Length(min=2, max=20)])
    submit = SubmitField("Sign Up")



class TaggingForm(FlaskForm):
    """
    Tagging form.
    """
    choices = SelectField("Hvem har skrevet dette tweet?")
    submit = SubmitField("Submit")


class TagButton(FlaskForm):
    """
    Tagging form.
    """
    submit = SubmitField("This doesn't matter apparently")

    def set_name(self, new_name):
        """
        Set name.
        """
        self.submit.label = Label("", new_name)


class AddTweetCategoryForm(FlaskForm):
    """
    Add tweet category form.
    """
    twitter_handle = StringField("Twitter handle", validators=[DataRequired()])
    submit = SubmitField("Create")





class AddProjectForm(FlaskForm):
    """
    Add project form.
    """
    title = StringField("Title", validators=[DataRequired()])
    description = StringField("Description", validators=[DataRequired()])
    categories = SelectMultipleField(
        "Categories for your students to work with", validators=[DataRequired()]
    )
    organization = SelectField(
        "Which student group should participate?", validators=[DataRequired()]
    )
    submit = SubmitField("Create Project")

    def validate_title(self, title):
        """
        Validate title.
        """
        title = Project.query.filter_by(name=title.data).first()
        if title:
            raise ValidationError("That project name is taken. Please choose a different one.")


class AddBayesianAnalysisForm(FlaskForm):
    """
    Add Bayesian analysis form.
    """
    name = StringField("Title of Analysis", validators=[DataRequired()])
    shared = BooleanField("Shared project?")
    shared_model = BooleanField("Shared Underlying Model?")
    annotate = SelectField("Annotate analysis?")
    number = IntegerField("How many of each category?")
    submit = SubmitField("Create Analysis")


class RunBayesianAnalysisRobot(FlaskForm):
    """
    Run Bayesian analysis robot form.
    """
    run_analysis = SubmitField("Run Model!")


class AddBayesianRobotForm(FlaskForm):
    """
    Add Bayesian robot form.
    """
    name = StringField("Title of Robot", validators=[DataRequired()])
    submit = SubmitField("Create New Robot")


class CreateMatrixForm(FlaskForm):
    """
    Create matrix form.
    """
    categories = SelectMultipleField("Categories to compare", validators=[DataRequired()])
    ratio = IntegerField("Training tweets proportion (%)", validators=[DataRequired()])
    submit = SubmitField("Create Matrix")


class ThresholdForm(FlaskForm):
    """
    Threshold form.
    """
    shuffle = BooleanField("Shuffle tweets")
    threshold = FloatField("Set a threshold between 0 and 1")
    ratio = IntegerField("Change training tweets proportion (%)")
    submit = SubmitField("Update")


class AnalysisForm(FlaskForm):
    """
    Analysis form.
    """
    robort_form = FormField(AddBayesianRobotForm)
    add_category_form = FormField(AddTweetCategoryForm)


class AddBayesianRobotFeatureForm(FlaskForm):
    """
    Add Bayesian robot feature form.
    """
    feature = StringField(
        "Add a feature to your machine learning model here. You can use wildcard (*) to search for more words. You can add wildcard in the middle or at the beginning or end of your word. Only one wildcard per search term." # pylint: disable=line-too-long
    )
    reasoning = StringField(
        "Explain here why you think this would be a good search term for classifying these texts."
    )
    submit = SubmitField("Add Term")


class BayesianRobotForms(FlaskForm):
    """
    Bayesian robot forms.
    """
    add_feature_form = FormField(AddBayesianRobotFeatureForm)
    run_analysis_form = FormField(RunBayesianAnalysisRobot)





class PostForm(FlaskForm):
    """
    Post form.
    """
    title = StringField("Title", validators=[DataRequired()])
    content = TextAreaField("Content", validators=[DataRequired()])
    submit = SubmitField("Post")


class AddOrgForm(FlaskForm):
    """
    Add organization form.
    """
    name = StringField("Name", validators=[DataRequired()])
    submit = SubmitField("Add Organization")


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


class AnnotationForm(FlaskForm):
    """
    Annotation form.
    """
    text = TextAreaField("selectedtext", validators=[DataRequired()])
    start = IntegerField("start")
    end = IntegerField("end")
    hidden = HiddenField()
    submit = SubmitField("save text")


class SelectCategoryForm(FlaskForm):
    """
    Select category form.
    """
    category = IntegerField("cat_id")
    submit = SubmitField("select category")
