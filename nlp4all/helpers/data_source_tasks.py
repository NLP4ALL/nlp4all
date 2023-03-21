"""Celery background tasks for data sources."""

import logging
import traceback
import typing as t
import json
import csv
from pathlib import Path
from time import sleep
from celery import shared_task, Task
from .. import db, conf
from ..models import DataSourceModel, DataModel, BackgroundTaskModel
from ..database import BackgroundTaskStatus
from sqlalchemy import select, text, bindparam, String
from sqlalchemy.engine import CursorResult
from sqlalchemy.orm import scoped_session, joinedload
from .data_source import (
    csv_row_to_json,
    generate_schema,
    schema_builder,
    minimum_paths_for_deletion,
    schema_path_index_and_keys_for_pgsql
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
        reader = f
    session: scoped_session = db.session
    af = session.autoflush
    session.autoflush = False
    task = ds.task
    # session.expire(task)
    for data_item in reader:
        if is_csv:
            data_item = csv_row_to_json(data_item, header)
        else:
            data_item = json.loads(data_item)
        schema = generate_schema(data_item, builder)
        data_model = DataModel(
            data_source=ds,
            document=data_item
        )

        session.add(data_model)
        data_processed += 1
        if data_processed % 1000 == 0:
            session.commit()
        elif data_processed % 50 == 0:
            nested = session.begin_nested()
            task.current_step = data_processed
            nested.commit()
            nested.close()

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
    task.task_status = BackgroundTaskStatus.STARTED
    db.session.commit()
    paths = data_source.path_aliases_from_schema()

    selected_paths = {field: paths[field] for field in selected_fields}

    paths_to_remove = minimum_paths_for_deletion(selected_paths, paths)

    logging.info("Selected paths: " + str(selected_paths))
    logging.info("Paths to remove: " + str(paths_to_remove))

    num_data_items = db.session.query(DataModel).filter(
        DataModel.data_source_id == data_source_id).count()
    task.total_steps = num_data_items * len(paths_to_remove)
    db.session.commit()

    updated_rows: int = 0
    try:
        main_query: str = """
WITH paths (id,path_arr) AS
    (SELECT id, path_arr
        FROM
            (SELECT id,document,jsonb_paths(document) path_arr
                FROM
                    {data_table} WHERE data_source_id=:data_source_id) c
        WHERE
            {where_clause})
UPDATE {data_table} a
    SET document = a.document #- b.path_arr
    FROM paths as b WHERE a.id=b.id;
"""
        data_table = DataModel.__tablename__
        sess: scoped_session = db.session
        # TODO: combine into one single massive where clause
        # currently it's extremely slow, and it could be for many reasons
        # also TODO: look up indexing for jsonb
        # https://www.postgresql.org/docs/current/datatype-json.html#JSON-INDEXING
        # currently it's running about 1 query / 5 minutes (at least the first few,
        # after which it gets a bit quicker), but intuitively,
        # it's probably almost exactly the same amount of time as doing all
        # the queries in one go
        for path_tuple in paths_to_remove.values():
            # jsonb_path = schema_path_to_jsonb_path(path_tuple)
            path_indices = schema_path_index_and_keys_for_pgsql(path_tuple)
            where_clause = " AND ".join(
                f"path_arr[{i}]=:path_key_{i}" for i, _ in path_indices)
            path_keys = {"path_key_" + str(i): key for i, key in path_indices}
            query = text(main_query.format(
                data_table=data_table,
                where_clause=where_clause
            ))

            query = query.bindparams(
                data_source_id=data_source_id,
                **path_keys
            )
            logging.info(query)
            result: CursorResult = sess.execute(query)  # type: ignore
            if result.rowcount > 0:
                updated_rows += result.rowcount
            task.current_step = updated_rows
            task.status_message = "Data source pruned successfully"
            sess.commit()
        task.task_status = BackgroundTaskStatus.SUCCESS
        sess.commit()

    except Exception as e:
        logging.info("Error pruning data source: " + str(e))
        logging.info(traceback.format_exc())
        task.current_step = updated_rows
        task.task_status = BackgroundTaskStatus.FAILURE
        task.status_message = str(e)
    logging.info("Updated rows: " + str(updated_rows))
    db.session.commit()
