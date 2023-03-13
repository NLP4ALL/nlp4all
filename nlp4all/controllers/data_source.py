"""Data sources."""  # pylint: disable=invalid-name

import os
from datetime import datetime
from flask import redirect, url_for
from flask_login import current_user
from werkzeug.utils import secure_filename
from .base import BaseController
from ..forms.data_source import AddDataSourceForm, ConfigureDataSourceForm
from ..models import DataSourceModel, BackgroundTaskModel
from .. import db, conf
from ..helpers.data_source_tasks import process_data_source
from ..database import BackgroundTaskStatus


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
            destination = os.path.join(
                conf.DATA_UPLOAD_DIR,
                filename)

            # if the file exists we can add a timestamp to the filename
            while os.path.exists(destination):
                ts = datetime.now().strftime("%Y%m%d%H%M%S")
                filename = f"{os.path.splitext(filename)[0]}_{ts}{os.path.splitext(filename)[1]}"
                destination = os.path.join(
                    conf.DATA_UPLOAD_DIR,
                    filename)

            f.save(destination)
            ds = DataSourceModel(
                data_source_name=form.data_source_name.data,
                user=current_user,
                user_id=current_user.id,  # type: ignore
                filename=filename)
            db.session.add(ds)
            db.session.commit()
            task_result = process_data_source.delay(ds.id)  # type: ignore
            bg = BackgroundTaskModel(
                task_id=task_result.id,
            )
            db.session.add(bg)
            db.session.commit()
            ds.task_id = bg.id
            db.session.commit()
            return redirect(url_for("datasource_controller.configure", datasource_id=ds.id))
        return cls.render_template("data_source_add.html", title="New Data Source", form=form)

    @classmethod
    def configure(cls, datasource_id: int):
        """Specify data fields"""
        ds = db.session.query(DataSourceModel).filter_by(id=datasource_id).first()
        task = ds.task
        if task.task_status in [BackgroundTaskStatus.PENDING, BackgroundTaskStatus.STARTED]:
            return cls.render_template(
                "data_source_processing.html",
                title="Data source processing",
                ds=ds,
                task=task
            )
        form = ConfigureDataSourceForm()
        form.data_source_fields.choices = [f for f in ds.path_aliases_from_schema().keys()]
        form.data_source_main.choices = ['Pick a primary text field...'] + form.data_source_fields.choices
        if form.validate_on_submit():
            return redirect(url_for("datasource_controller.configure", datasource_id=ds.id, step=""))

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
