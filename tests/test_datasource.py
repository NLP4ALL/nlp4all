"""Tests for datasources"""

import datetime
import os
from typing import Union
import unittest

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    Integer,
    String,
)

from nlp4all.models import DataSourceManager, ColTypeSQL, ColType

# pylint: disable=protected-access


class TestEnums(unittest.TestCase):
    """Tests for ColType and ColTypeSQL enums"""

    def test_coltype(self):
        """test ColType enum"""

        self.assertEqual(ColType.BOOLEAN.value, "boolean")
        self.assertEqual(ColType.DATETIME.value, "datetime")
        self.assertEqual(ColType.FLOAT.value, "float")
        self.assertEqual(ColType.ID.value, "id")
        self.assertEqual(ColType.INTEGER.value, "integer")
        self.assertEqual(ColType.STRING.value, "string")
        self.assertEqual(ColType.TEXT.value, "text")

    def test_coltype_from_str(self):
        """test ColType enum from string"""

        self.assertEqual(ColType.from_str("boolean"), ColType.BOOLEAN)
        self.assertEqual(ColType.from_str("datetime"), ColType.DATETIME)
        self.assertEqual(ColType.from_str("float"), ColType.FLOAT)
        self.assertEqual(ColType.from_str("id"), ColType.ID)
        self.assertEqual(ColType.from_str("integer"), ColType.INTEGER)
        self.assertEqual(ColType.from_str("string"), ColType.STRING)
        self.assertEqual(ColType.from_str("text"), ColType.TEXT)

    def test_coltype_sql(self):
        """test ColTypeSQL enum"""

        self.assertEqual(ColTypeSQL.BOOLEAN.value, Boolean)
        self.assertEqual(ColTypeSQL.DATETIME.value, DateTime)
        self.assertEqual(ColTypeSQL.FLOAT.value, Float)
        self.assertEqual(ColTypeSQL.ID.value, Integer)
        self.assertEqual(ColTypeSQL.INTEGER.value, Integer)
        self.assertEqual(ColTypeSQL.STRING.value, String)
        self.assertEqual(ColTypeSQL.TEXT.value, String)

    def test_coltype_sql_from_coltype(self):
        """test ColTypeSQL enum from ColType"""

        self.assertEqual(ColTypeSQL.from_coltype(ColType.BOOLEAN), ColTypeSQL.BOOLEAN)
        self.assertEqual(ColTypeSQL.from_coltype(ColType.DATETIME), ColTypeSQL.DATETIME)
        self.assertEqual(ColTypeSQL.from_coltype(ColType.FLOAT), ColTypeSQL.FLOAT)
        self.assertEqual(ColTypeSQL.from_coltype(ColType.ID), ColTypeSQL.ID)
        self.assertEqual(ColTypeSQL.from_coltype(ColType.INTEGER), ColTypeSQL.INTEGER)
        self.assertEqual(ColTypeSQL.from_coltype(ColType.STRING), ColTypeSQL.STRING)
        self.assertEqual(ColTypeSQL.from_coltype(ColType.TEXT), ColTypeSQL.TEXT)


class TestDataSourceManager(unittest.TestCase):
    """Tests for DataSourceManager"""

    dsm: Union[DataSourceManager, None] = None
    user_id: int = 1
    data_source_id: int = 99
    test_colspec: dict = {
        "id": ColType.ID,
        "col1": ColType.STRING,
        "col2": ColType.INTEGER,
        "col3": ColType.FLOAT,
        "col4": ColType.BOOLEAN,
        "col5": ColType.DATETIME,
        "maintext": ColType.TEXT,
    }

    def is_row_in_db(self, row_dict: dict) -> bool:
        """Check if row is in database"""
        with self.dsm.session() as ds_sess:
            uds = self.dsm.get_data_source_class()
            # check values in the database
            for col, value in row_dict.items():
                assert getattr(ds_sess.query(uds).first(), col) == value

        return True

    def create_dsm(self):
        """Create simple dsm"""
        self.dsm = DataSourceManager(self.data_source_id, self.user_id)

    def destroy_dsm(self):
        """Destroy dsm"""

        if self.dsm is not None:
            self.dsm.delete_data_source()
            self.dsm = None

    def test_connect(self):
        """Test connect"""
        self.create_dsm()
        assert self.dsm is not None
        assert self.dsm._data_source_id == self.data_source_id
        assert self.dsm._user_id == self.user_id
        assert self.dsm._connected is False
        assert self.dsm._filename is not None
        self.dsm.connect()
        assert self.dsm._connected is True
        assert os.path.exists(self.dsm._filename)
        assert self.dsm._engine is not None
        # assert self.dsm._table is None
        assert self.dsm._meta_table is not None
        self.destroy_dsm()

    def test_delete_data_source(self):
        """Test delete_data_source"""
        self.create_dsm()
        self.dsm.connect()
        assert self.dsm._connected is True
        assert os.path.exists(self.dsm._filename)
        self.dsm.delete_data_source()
        assert self.dsm._connected is False
        assert not os.path.exists(self.dsm._filename)
        self.dsm = None

    def test_create_table(self):
        """Test create_table"""
        self.create_dsm()
        self.dsm.connect()
        self.dsm.create_table(self.test_colspec)
        assert self.dsm._colspec is not None
        assert self.dsm._colspec == {
            "id": ColType.ID,
            "col1": ColType.STRING,
            "col2": ColType.INTEGER,
            "col3": ColType.FLOAT,
            "col4": ColType.BOOLEAN,
            "col5": ColType.DATETIME,
            "maintext": ColType.TEXT,
        }

        assert self.dsm._table.columns.keys() == list(self.dsm._colspec.keys())

        for col, coltype in self.test_colspec.items():
            assert issubclass(
                self.dsm._table.columns[col].type.__class__,
                ColTypeSQL.from_coltype(coltype).value,
            )

        self.destroy_dsm()

    def test_add_row_syntax_1(self):
        """Test add_row syntax 1"""
        self.create_dsm()
        self.dsm.connect()
        self.dsm.create_table(self.test_colspec)

        uds = self.dsm.get_data_source_class()
        assert uds is not None

        with self.dsm.session() as ds_sess:
            assert ds_sess is not None

            uds_instance = uds()
            assert uds_instance is not None

            test_row = {
                "col1": "string1",
                "col2": 1,
                "col3": 1.0,
                "col4": True,
                "col5": datetime.datetime.now(),
                "maintext": "text1",
            }

            uds_instance.values_from_dict(test_row)

            ds_sess.add(uds_instance)

            ds_sess.commit()

        assert self.is_row_in_db(test_row)

        self.destroy_dsm()

    def test_add_row_syntax_2(self):
        """Test add_row syntax 2"""
        self.create_dsm()
        self.dsm.connect()
        self.dsm.create_table(self.test_colspec)

        uds = self.dsm.get_data_source_class()
        assert uds is not None

        with self.dsm.session() as ds_sess:
            assert ds_sess is not None

            test_row = {
                "col1": "string2",
                "col2": 2,
                "col3": 2.0,
                "col4": False,
                "col5": datetime.datetime.now(),
                "maintext": "text2",
            }

            uds_instance = uds(**test_row)

            ds_sess.add(uds_instance)

            ds_sess.commit()

            assert self.is_row_in_db(test_row)

            self.destroy_dsm()

    def test_add_row_syntax_3(self):
        """Test add_row syntax 3"""
        self.create_dsm()
        self.dsm.connect()
        self.dsm.create_table(self.test_colspec)

        uds = self.dsm.get_data_source_class()
        assert uds is not None
        with self.dsm.session() as ds_sess:
            assert ds_sess is not None

            test_row = {
                "col1": "string3",
                "col2": 3,
                "col3": 3.0,
                "col4": True,
                "col5": datetime.datetime.now(),
                "maintext": "text3",
            }

            uds_instance = uds()
            assert uds_instance is not None

            uds_instance.col1 = test_row["col1"]
            uds_instance.col2 = test_row["col2"]
            uds_instance.col3 = test_row["col3"]
            uds_instance.col4 = test_row["col4"]
            uds_instance.col5 = test_row["col5"]
            uds_instance.maintext = test_row["maintext"]

            ds_sess.add(uds_instance)

            ds_sess.commit()

        assert self.is_row_in_db(test_row)

        self.destroy_dsm()
