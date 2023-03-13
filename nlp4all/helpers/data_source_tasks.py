"""Celery background tasks for data sources."""

import typing as t
import json
from pathlib import Path
from time import sleep
from celery import shared_task
from .. import db, conf
from ..models import DataSourceModel, DataModel, BackgroundTaskModel
from ..database import BackgroundTaskStatus
from sqlalchemy import select
from .data_source import csv_file_to_json, generate_schema


def load_data_file(ds: DataSourceModel) -> None:
    """Load the data file."""

    file_path = Path(
        conf.DATA_UPLOAD_DIR,
        ds.filename)

    if file_path.suffix.lower() in [".csv", ".tsv", ".txt"]:
        data = csv_file_to_json(file_path)
    elif file_path.suffix.lower() == ".json":
        data = json.load(file_path.open())
    else:
        raise RuntimeError("Unsupported file type")

    schema = generate_schema(data)
    ds.schema = schema
    data_processed = 0
    ds.task.total_steps = len(data)
    # @TODO: consider using a bulk insert here
    for data_item in data:
        data_model = DataModel(
            data_source=ds,
            document=data_item
        )
        db.session.add(data_model)
        data_processed += 1
        ds.task.current_step = data_processed
        db.session.commit()


@shared_task(ignore_result=False)
def process_data_source(data_source_id: int) -> None:
    """Process a data source."""
    # we should allow for a little delay with updating the DB
    attempts: int = 0
    data_source: t.Union[DataSourceModel, None] = None
    while True:
        stmt = select(DataSourceModel).filter_by(id=data_source_id)
        data_source = db.session.scalars(stmt).first()
        if data_source is None:
            raise RuntimeError("Unable to find data source with id: " + str(data_source_id))

        task: BackgroundTaskModel = data_source.task
        if task is None:
            sleep(secs=1)
            attempts += 1
            if attempts > 5:
                raise RuntimeError("Unable to update data source task status")

        if data_source.task.task_status != BackgroundTaskStatus.PENDING:
            return
        break
    task = data_source.task
    task.task_status = BackgroundTaskStatus.STARTED
    db.session.commit()
    try:
        load_data_file(data_source)
        task.task_status = BackgroundTaskStatus.SUCCESS
        task.status_message = "Data source processed successfully"
    except Exception as e:
        task.task_status = BackgroundTaskStatus.FAILURE
        task.status_message = str(e)
        # delete all data items
        db.session.query(DataModel).filter(
            DataModel.data_source_id == data_source_id).delete()
    db.session.commit()
