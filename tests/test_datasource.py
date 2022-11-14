"""Tests for datasources"""

import datetime
import os
import unittest
import pytest

from nlp4all.models import DataSourceManager, ColTypeSQL, ColType

# pylint: disable=protected-access
class TestDataSourceManager(unittest.TestCase):
    """Tests for DataSourceManager"""

    @pytest.mark.data
    def test_datasource_manager(self):
        """Test DataSourceManager"""

        colspec = {
                "id": ColType.ID,
                "col1": ColType.STRING,
                "col2": ColType.INTEGER,
                "col3": ColType.FLOAT,
                "col4": ColType.BOOLEAN,
                "col5": ColType.DATETIME,
                "maintext": ColType.TEXT
            }

        datasource_manager = DataSourceManager(
            user_id=1,
            data_source_name="test"
        )

        datasource_manager.connect()
        datasource_manager.create_table(colspec)

        assert datasource_manager._engine is not None
        assert datasource_manager._session is not None
        assert datasource_manager._table is not None
        assert datasource_manager._meta_table is not None
        assert datasource_manager._colspec is not None
        assert datasource_manager._user_id == 1
        assert datasource_manager._data_source_name == "test"
        assert datasource_manager._colspec == {
            "id": ColType.ID,
            "col1": ColType.STRING,
            "col2": ColType.INTEGER,
            "col3": ColType.FLOAT,
            "col4": ColType.BOOLEAN,
            "col5": ColType.DATETIME,
            "maintext": ColType.TEXT
        }

        assert datasource_manager._table.columns.keys() == list(datasource_manager._colspec.keys())
        assert issubclass(
            datasource_manager._table.columns["id"].type.__class__,
            ColTypeSQL.INTEGER.value)
        assert issubclass(
            datasource_manager._table.columns["col1"].type.__class__,
            ColTypeSQL.STRING.value)
        assert issubclass(
            datasource_manager._table.columns["col2"].type.__class__,
            ColTypeSQL.INTEGER.value)
        assert issubclass(
            datasource_manager._table.columns["col3"].type.__class__,
            ColTypeSQL.FLOAT.value)
        assert issubclass(
            datasource_manager._table.columns["col4"].type.__class__,
            ColTypeSQL.BOOLEAN.value)
        assert issubclass(
            datasource_manager._table.columns["col5"].type.__class__,
            ColTypeSQL.DATETIME.value)
        assert issubclass(
            datasource_manager._table.columns["maintext"].type.__class__,
            ColTypeSQL.TEXT.value)

        uds = datasource_manager.get_data_source_class()
        assert uds is not None

        uds_instance = uds()
        assert uds_instance is not None

        uds_instance.row_dict(
            {
                "col1": "string",
                "col2": 1,
                "col3": 1.0,
                "col4": True,
                "col5": datetime.datetime.now(),
                "maintext": "text"
            }
        )

        ds_sess = datasource_manager.get_session()

        ds_sess.add(uds_instance)

        ds_sess.commit()

        # try using sqlalchemy method
        uds_new_instance = uds()
        uds_new_instance.col1 = "string2"
        uds_new_instance.col2 = 2
        uds_new_instance.col3 = 2.0
        uds_new_instance.col4 = False
        uds_new_instance.col5 = datetime.datetime.now()
        uds_new_instance.maintext = "text2"

        ds_sess.add(uds_new_instance)
        ds_sess.commit()

        # try using sqlalchemy method
        uds_new_instance = uds(
            col1="string3",
            col2=3,
            col3=3.0,
            col4=True,
            col5=datetime.datetime.now(),
            maintext="text3"
        )

        ds_sess.add(uds_new_instance)
        ds_sess.commit()


        # delete and ensure file is gone
        filename = datasource_manager._filename
        datasource_manager.delete_data_source()
        assert not os.path.exists(filename)
