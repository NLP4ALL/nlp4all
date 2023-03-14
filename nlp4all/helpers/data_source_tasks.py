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
from sqlalchemy.orm import scoped_session
# from sqlalchemy import func
from .data_source import (
    csv_file_to_json,
    generate_schema,
    minimum_paths_for_deletion,
    schema_path_to_jsonb_path
)


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
    ds.aliased_paths = ds.path_aliases_from_schema()
    db.session.commit()


def wait_for_data_source(data_source_id: int) -> t.Tuple[DataSourceModel, BackgroundTaskModel]:
    """Wait for a data source/task to be available."""
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
            continue
        break
    return data_source, task


@shared_task(ignore_result=False)
def process_data_source(data_source_id: int) -> None:
    """Process a data source."""
    data_source, task = wait_for_data_source(data_source_id)
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
        db.session.query(DataModel).filter(
            DataModel.data_source_id == data_source_id).delete()
    db.session.commit()


@shared_task(ignore_result=False)
def prune_data_source(data_source_id: int, selected_fields: t.Collection[str]) -> None:
    """Prune data source.

    This removes fields that were not selected by the user.
    """
    data_source, task = wait_for_data_source(data_source_id)
    if task.task_status != BackgroundTaskStatus.PENDING:
        return
    task.task_status = BackgroundTaskStatus.STARTED
    db.session.commit()
    paths = data_source.aliased_paths
    selected_paths = {field: paths[field] for field in selected_fields}

    paths_to_remove = minimum_paths_for_deletion(selected_paths, paths)

    # reference query
    # with paths(id,path_arr) as
    #         (select id, path_arr from
    #             (select id,document,jsonb_paths(document) path_arr from
    #                 nlp_data where data_source_id={data_source_id}) c
    #             where
    # (path_arr[1]='path_part_obj' and path_arr[2]='path_part_sub_obj')
    # or (path_arr[1]='path_part_obj' and path_arr[3]='path_part_obj_under_array')
    #     update nlp_data a
    #         set document = a.document #- b.path_arr
    #         from paths as b where a.id=b.id;


    try:
        main_query: str = """
WITH paths (id,path_arr) AS
    (SELECT id, path_arr
        FROM
            (SELECT id,document,jsonb_paths(document) path_arr
                FROM
                    {:data_table} WHERE data_source_id={:data_source_id}) c
        WHERE
            (path_arr[1]='path_part_obj' AND path_arr[2]='path_part_sub_obj')
        or (path_arr[1]='path_part_obj' AND path_arr[3]='path_part_obj_under_array')
UPDATE {:data_table} a
    SET document = a.document #- b.path_arr
    FROM paths as b WHERE a.id=b.id;
"""
        for path_tuple in paths_to_remove.values():
            sess: scoped_session = db.session
            jsonb_path = schema_path_to_jsonb_path(path_tuple)
            sess.execute(
                f"update nlp_data set document=document #- '{jsonb_path}' where data_source_id={data_source_id}")
            
        db.session.commit()
        task.task_status = BackgroundTaskStatus.SUCCESS
        task.status_message = "Data source pruned successfully"
    except Exception as e:
        task.task_status = BackgroundTaskStatus.FAILURE
        task.status_message = str(e)
    db.session.commit()
