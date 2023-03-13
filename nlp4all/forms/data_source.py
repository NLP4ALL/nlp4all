"""Forms for datasource manipulation / creation etc"""

from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    SubmitField,
    FileField,
    TextAreaField,
    SelectMultipleField,
    SelectField
)
from wtforms.validators import DataRequired, NoneOf
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

    data_source_main = SelectField(
        "Which field contains the main document text?",
        validators=[
            DataRequired(),
            NoneOf(["Pick a primary text field..."])
        ])
    data_source_fields = SelectMultipleField(
        "Which additional fields should be used?",
        validators=[
            DataRequired()
        ])
    submit = SubmitField("Next")
