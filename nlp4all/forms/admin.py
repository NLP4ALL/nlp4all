"""Admin related forms"""

from flask_wtf import FlaskForm

from wtforms import (
    StringField,
    SubmitField,
    SelectMultipleField,
    SelectField,
)

from wtforms.validators import DataRequired, ValidationError
from ..models import ProjectModel


class AddOrgForm(FlaskForm):
    """
    Add group form.
    """

    name = StringField("Name", validators=[DataRequired()])
    submit = SubmitField("Add Group")


class AddProjectForm(FlaskForm):
    """
    Add project form.
    """

    title = StringField("Title", validators=[DataRequired()])
    description = StringField("Description", validators=[DataRequired()])
    categories = SelectMultipleField(
        "Categories for your students to work with", validators=[DataRequired()]
    )
    group = SelectField(
        "Which student group should participate?", validators=[DataRequired()]
    )
    submit = SubmitField("Create Project")

    def validate_title(self, title):
        """
        Validate title.
        """
        title = ProjectModel.query.filter_by(name=title.data).first()
        if title:
            raise ValidationError("That project name is taken. Please choose a different one.")
