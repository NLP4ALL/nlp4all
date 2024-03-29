"""Celery background tasks for data sources."""

import logging
import traceback
import typing as t
import json
import csv
from pathlib import Path
from celery import shared_task, Task
from .. import db, conf, docdb
from ..models import DataSourceModel, DataModel, BackgroundTaskModel
from ..database import BackgroundTaskStatus
from sqlalchemy import select
from sqlalchemy.orm import scoped_session
from .data_source import (
    csv_row_to_json,
    generate_schema,
    schema_builder,
    remove_paths_from_schema,
    minimum_paths_for_deletion,
    schema_path_to_jsonb_path,
    schema_aliased_path_dict
)


def buf_count_newlines_gen(fname):
    def _make_gen(reader):
        while True:
            b = reader(2 ** 16)
            if not b:
                break
            yield b

    with open(fname, "rb") as f:
        count = sum(buf.count(b"\n") for buf in _make_gen(f.raw.read))
    return count


def load_data_file(ds: DataSourceModel) -> None:
    """Load the data file."""

    file_path = Path(
        conf.DATA_UPLOAD_DIR,
        ds.filename)

    if not file_path.exists():
        raise RuntimeError("File not found")

    if file_path.suffix.lower() not in [".csv", ".tsv", ".txt", ".json"]:
        raise RuntimeError("Unsupported file type")
    # if file_path.suffix.lower() in [".csv", ".tsv", ".txt"]:
    #     data = csv_file_to_json(file_path)
    # elif file_path.suffix.lower() == ".json":
    #     data = json.load(file_path.open())
    # else:
    #     raise RuntimeError("Unsupported file type")

    # schema = generate_schema(data)
    # ds.schema = schema
    is_csv = False if file_path.suffix.lower() == ".json" else True
    data_processed = 0
    ds.task.total_steps = buf_count_newlines_gen(str(file_path))
    # @TODO: consider using a bulk insert here
    builder = schema_builder()
    f = file_path.open()
    schema = None
    if is_csv:
        reader = csv.reader(f)
        header = next(reader)
        data_processed += 1
    else:
        reader = f  # type: ignore
    session: scoped_session = db.session
    af = session.autoflush
    session.autoflush = False
    task = ds.task
    ds_collection = docdb.get_collection(ds.collection_name)
    # session.expire(task)
    process_every = 100
    update_every = 1000
    data_items = []
    for data_item in reader:
        if is_csv:
            data_item = csv_row_to_json(data_item, header)  # type: ignore
        else:
            data_item = json.loads(data_item)  # type: ignore
        # data_model = DataModel(
        #     data_source=ds,
        #     document=data_item
        # )

        # session.add(data_model)
        data_processed += 1
        data_items.append(data_item)
        if data_processed % process_every == 0:
            schema = generate_schema(data_items, builder)  # type: ignore
            ds_collection.insert_many(data_items)
            data_items = []
        if data_processed % update_every == 0:
            task.current_step = data_processed
            session.commit()
    if len(data_items) > 0:
        schema = generate_schema(data_items, builder)  # type: ignore
        ds_collection.insert_many(data_items)
        task.current_step = data_processed
        session.commit()

    if schema is not None:
        ds.schema = schema
        ds.aliased_paths = ds.path_aliases_from_schema()

    f.close()

    # delete the file
    file_path.unlink()
    session.autoflush = af


def wait_for_data_source(data_source_id: int, task_id: str) -> t.Tuple[DataSourceModel, BackgroundTaskModel]:
    """Wait for a data source/task to be available."""
    # we should allow for a little delay with updating the DB
    stmt = select(DataSourceModel).filter_by(id=data_source_id)
    data_source = db.session.scalars(stmt).first()
    if data_source is None:
        raise RuntimeError("Unable to find data source with id: " + str(data_source_id))
    task = BackgroundTaskModel(
        task_id=task_id,
        task_status=BackgroundTaskStatus.PENDING,
        total_steps=0,
        current_step=0,
    )
    db.session.add(task)
    db.session.commit()
    data_source.task_id = task.id
    db.session.commit()
    return data_source, task


@shared_task(ignore_result=True, bind=True)
def process_data_source(self: Task, data_source_id: int) -> None:
    """Process a data source."""
    data_source: t.Union[DataSourceModel, None] = None
    try:
        data_source, task = wait_for_data_source(data_source_id, self.request.id)
    except Exception as e:
        task = db.session.query(BackgroundTaskModel).filter_by(task_id=self.request.id).first()
        if task is None:
            task = BackgroundTaskModel(
                task_id=self.request.id,
            )
            db.session.add(task)
        task.task_status = BackgroundTaskStatus.FAILURE
        task.status_message = str(e)
        db.session.commit()
        if data_source is not None:
            data_source.task = task
            db.session.commit()
        return
    if task.task_status != BackgroundTaskStatus.PENDING:
        return
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
        filename = Path(conf.DATA_UPLOAD_DIR, data_source.filename)
        if filename.exists():
            filename.unlink()
        db.session.query(DataModel).filter(
            DataModel.data_source_id == data_source_id).delete()
    db.session.commit()


@shared_task(ignore_result=True, bind=True)
def prune_data_source(self: Task, data_source_id: int, selected_fields: t.Collection[str]) -> None:
    """Prune data source.

    This removes fields that were not selected by the user.
    """
    data_source, task = wait_for_data_source(data_source_id, self.request.id)
    if task.task_status != BackgroundTaskStatus.PENDING:
        return
    sess: scoped_session = db.session
    task.task_status = BackgroundTaskStatus.STARTED
    sess.commit()
    paths = data_source.path_aliases_from_schema()

    selected_paths = {field: paths[field] for field in selected_fields}

    paths_to_remove = minimum_paths_for_deletion(selected_paths, paths)

    logging.info("Selected paths: " + str(selected_paths))
    logging.info("Paths to remove: " + str(paths_to_remove))

    ds_collection = docdb.get_collection(data_source.collection_name)
    update_count = 0
    update_every = 1
    try:
        for path, path_tuple in paths_to_remove.items():
            logging.info("Removing path: " + path)
            jsonb_path = schema_path_to_jsonb_path(path_tuple)
            result = ds_collection.update_many(
                {path: {"$exists": True}},
                {"$unset": {jsonb_path: ""}}
            )
            update_count += result.modified_count
            if update_count % update_every == 0:
                task.current_step = update_count
                sess.commit()
            logging.info("Removed path: " + path)
        task.status_message = "Data source pruned successfully"
        task.task_status = BackgroundTaskStatus.SUCCESS
        data_source.schema = remove_paths_from_schema(data_source.schema, paths_to_remove)
        sess.commit()
    except Exception as e:
        logging.info("Error pruning data source: " + str(e))
        logging.info(traceback.format_exc())
        task.task_status = BackgroundTaskStatus.FAILURE
        task.status_message = str(e)
    # now we can add indices for the remaining paths
    try:
        docdb.add_indices_to_collection(
            ds_collection,
            schema_aliased_path_dict(data_source.schema, types_only=True),
            data_source.document_text_field)
    except Exception as e:
        logging.info("Error adding indices to collection: " + str(e))
        logging.info(traceback.format_exc())
        task.task_status = BackgroundTaskStatus.FAILURE
        task.status_message = str(e)
    db.session.commit()
