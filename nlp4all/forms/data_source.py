"""Forms for datasource manipulation / creation etc"""

from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    SubmitField,
    FileField,
    TextAreaField,
    SelectMultipleField,
)
from wtforms.validators import DataRequired
from flask_wtf.file import FileRequired, FileAllowed


class AddDataSourceForm(FlaskForm):
    """
    Add data source form.
    """

    data_source_name = StringField(
        "Name",
        validators=[
            DataRequired()
        ])
    data_source_description = TextAreaField("Description")
    data_source = FileField(
        "Data source",
        validators=[
            FileAllowed(["csv", "tsv", "json", "txt"], "Only csv, tsv, json and txt files are allowed"),
            FileRequired("Please select a file.")
        ])
    submit = SubmitField("Create")


class ConfigureDataSourceForm(FlaskForm):
    """
    Configure data source.
    """

    data_source_fields = SelectMultipleField(
        "Which fields should be used?",
        validators=[
            DataRequired()
        ])
    submit = SubmitField("Next")
