"""Data sources."""  # pylint: disable=invalid-name

import os
from datetime import datetime
from flask import redirect, url_for, current_app
from werkzeug.utils import secure_filename
from .base import BaseController
from ..forms.data_source import AddDataSourceForm, ConfigureDataSourceForm
from ..models import DataSourceModel
from .. import db


class DataSourceController(BaseController):  # pylint: disable=too-few-public-methods
    """Data Source Controller"""

    view_subdir = "datasource"

    @classmethod
    def home(cls):
        """List of prepared data source"""
        datasources = db.session.query(DataSourceModel).all()
        return cls.render_template("data_source_list.html", title="My Data Sources", datasources=datasources)

    @classmethod
    def create(cls):
        """Upload / create page"""
        form = AddDataSourceForm()
        if form.validate_on_submit():
            f = form.data_source.data
            filename = secure_filename(f.filename)
            destination = os.path.join(current_app.root_path, 'data', filename)
            # if the file exists we can add a timestamp to the filename
            while os.path.exists(destination):
                ts = datetime.now().strftime("%Y%m%d%H%M%S")
                filename = f"{os.path.splitext(filename)[0]}_{ts}{os.path.splitext(filename)[1]}"
                destination = os.path.join(current_app.root_path, 'data', filename)

            f.save(destination)
            ds = DataSourceModel(
                data_source_name=form.data_source_name.data,
                filename=filename)
            db.session.add(ds)
            db.session.commit()
            return redirect(url_for("datasource_controller.configure") + f"/{ds.id}")
        return cls.render_template("data_source_add.html", title="New Data Source", form=form)

    @classmethod
    def configure(cls, datasource_id: int):
        """Specify data fields"""
        ds = db.session.query(DataSourceModel).filter_by(id=datasource_id).first()
        form = ConfigureDataSourceForm()
        form.data_source_fields.choices = [(f, f) for f in ds.fields]
        return cls.render_template(
            "data_source_configure.html",
            title="Configure Data Source",
            ds=ds,
            form=form
        )

    @classmethod
    def save(cls):
        """Save data source"""
        return redirect(url_for("data_source_controller.home"))
