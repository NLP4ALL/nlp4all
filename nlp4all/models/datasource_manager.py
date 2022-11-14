"""datasource: this allows a dynamic engine to be used for an individual user data source"""

import hashlib

from enum import Enum
import os
from typing import Dict, List, Union

from sqlalchemy import (
    Boolean,
    Column,
    create_engine,
    DateTime,
    Float,
    Integer,
    inspect,
    JSON,
    MetaData,
    String,
    Table,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.engine.reflection import Inspector
from sqlalchemy.pool import NullPool
from sqlalchemy.engine import Engine
from sqlalchemy.orm import scoped_session, sessionmaker, mapper


class ColType(Enum):
    """Column types"""

    BOOLEAN = "boolean"
    DATETIME = "datetime"
    FLOAT = "float"
    ID = "id"
    INTEGER = "integer"
    STRING = "string"
    TEXT = "text"

    @staticmethod
    def get_type(col_type: str) -> "ColType":
        """Get the column type"""

        return ColType[col_type.upper()]


class ColTypeSQL(Enum):
    """Column types to map to SQLAlchemy types"""

    BOOLEAN = Boolean
    DATETIME = DateTime
    FLOAT = Float
    ID = Integer
    INTEGER = Integer
    STRING = String
    TEXT = String

    @staticmethod
    def from_coltype(coltype: ColType) -> "ColTypeSQL":
        """Convert a ColType to a ColTypeSQL"""

        coltype_sql = None

        if coltype == ColType.BOOLEAN:
            coltype_sql = ColTypeSQL.BOOLEAN
        if coltype == ColType.DATETIME:
            coltype_sql = ColTypeSQL.DATETIME
        if coltype == ColType.FLOAT:
            coltype_sql = ColTypeSQL.FLOAT
        if coltype == ColType.ID:
            coltype_sql = ColTypeSQL.ID
        if coltype == ColType.INTEGER:
            coltype_sql = ColTypeSQL.INTEGER
        if coltype == ColType.STRING:
            coltype_sql = ColTypeSQL.STRING
        if coltype == ColType.TEXT:
            coltype_sql = ColTypeSQL.STRING

        if coltype_sql is None:
            raise ValueError(f"Unknown coltype: {coltype}")

        return coltype_sql


class DataSourceManager: # pylint: disable=too-many-instance-attributes
    """DataSourceManager: this allows a dynamic engine to be used
    for an individual user data source. It handles the creation of
    the engine and the session, and the mapping of the table and columns.
    """

    _engine: Union[Engine, None] = None
    _session: Union[scoped_session, None] = None
    _table: Union[Table, None] = None
    _meta_table: Union[Table, None] = None
    _colspec: Union[Dict[str, ColType], None] = None
    _text_col_name: Union[str, None] = None
    _orm_meta: Union[None, MetaData] = None
    _inspect: Union[Inspector, None] = None
    _orm_base_class: Dict[str, object] = {}

    _user_id: int
    _data_source_name: str
    _filename: str
    _tablename: str
    _meta_table_name: str = "datasource_meta"

    _connected: bool = False

    def _set_datasource_meta_class(self):
        class UserDataSourceMeta(self._orm_base_class): # pylint: disable=too-few-public-methods
            """UserDataSourceMeta for table spec information"""

            __abstract__ = True

        self.UserDataSourceMeta = UserDataSourceMeta # pylint: disable=invalid-name

    def _set_datasource_class(self):
        class UserDataSource(self._orm_base_class): # pylint: disable=too-few-public-methods
            """UserDataSource
            This class is for using with sqlalchemy mapper.
            It can't be declared outside this class because
            it needs to be unique per instance of DataSourceManager.
            """

            __abstract__ = True

        self.UserDataSource = UserDataSource # pylint: disable=invalid-name

    def __init__(self, data_source_name: str, user_id: int) -> None:
        """Initialize the datasource manager"""

        self._data_source_name = data_source_name
        self._user_id = user_id
        self._set_base_class()
        self._set_datasource_class()
        self._set_datasource_meta_class()
        self._datasource_filename()

    def _set_base_class(self):
        """Set the base class for the table and meta table"""
        self._orm_base_class = declarative_base()

    def connect(self) -> None:
        """Connect to the datasource"""
        if self._engine is None:
            self._create_engine()
        self._inspect = inspect(self._engine)
        if self._session is None:
            self._create_session()
        self._orm_meta = MetaData(self._engine)
        self._connected = True
        self._load_tables()

    def disconnect(self) -> None:
        """Disconnect from the datasource"""

        if not self._connected:
            return

        self._session.close()
        self._session = None
        self._engine.dispose()
        self._engine = None
        self._connected = False

    def delete_data_source(self) -> None:
        """Delete a data source"""

        self.disconnect()

        # delete the file
        os.remove(self._filename)

    def get_text_column_name(self) -> str:
        """Get the name of the text column"""

        self._ensure_connected()

        return self._text_col_name

    def create_table(self, columns: Dict[str, ColType]) -> None:
        """Create a table in a user's datasource"""

        self._ensure_connected()

        # make sure there is a ColType.TEXT column, and only one
        text_col = None
        for colname, coltype in columns.items():
            if coltype == ColType.TEXT:
                if text_col is None:
                    text_col = colname
                else:
                    raise Exception("Only one column can be TEXT")
        if text_col is None:
            raise Exception("Must have one column of type TEXT")

        self._text_col_name = text_col

        created = self._create_datasource_table(columns)
        if created:
            self._map_datasource_table()

    def get_data_source_class(self) -> Union[None, type]:
        """Get the data source class for using with sqlalchemy"""

        self._ensure_connected()

        if self._colspec is None:
            return None

        return self.UserDataSource

    def get_session(self) -> scoped_session:
        """Get the session"""

        self._ensure_connected()

        return self._session

    def _ensure_connected(self) -> None:
        """Ensure we are connected to the datasource"""

        if not self._connected:
            raise Exception("Not connected to datasource")

    def _load_tables(self):
        """Load the tables"""

        self._ensure_connected()

        self._create_datasource_meta_table()
        self._map_datasource_meta_table()

        self._load_colspec()

        if not self._colspec is None:
            # if we get here, the table already exists
            self._create_datasource_table(self._colspec)
            self._map_datasource_table()

    def _load_colspec(self) -> None:
        """Load the column spec from the datasource meta table"""

        self._ensure_connected()

        colspec = self._session.query(self.UserDataSourceMeta).first()

        if colspec is not None:
            self._colspec = {}

            for colname, coltype in colspec.metaspec.items():
                self._colspec[colname] = ColType.get_type(coltype)

    def _save_colspec(self) -> None:
        """Save the column spec to the datasource meta table"""

        self._ensure_connected()

        colspec = {}
        for colname, coltype in self._colspec.items():
            colspec[colname] = coltype.value

        stmt = self._meta_table.insert().values(metaspec=colspec)

        result = self._session.execute(stmt)
        self._session.commit()
        result.close()

    def _datasource_filename(self) -> None:
        """Get the filename for specified datasource and user"""

        ds_dir = "data/user"

        if not os.path.exists(ds_dir):
            os.makedirs(ds_dir)
        # generate a unique filename from a hash of the data source id
        # this is to prevent a user from accessing another user's data
        ds_id_hash = hashlib.sha256(self._data_source_name.encode()).hexdigest()
        self._tablename = f"ds_{ds_id_hash}"
        self._filename = f"{ds_dir}/user_{self._user_id}_{ds_id_hash}.db"

    def _create_engine(self) -> None:
        """Create the engine for the datasource"""

        self._engine = create_engine(
            f"sqlite:///{self._filename}",
            connect_args={"check_same_thread": False},
            poolclass=NullPool,
        )

    def _create_session(self) -> None:
        """Get a session for a user's datasource"""

        db_session = scoped_session(
            sessionmaker(autocommit=False, autoflush=False, bind=self._engine)
        )

        self._session = db_session

    def _create_datasource_meta_table(self) -> None:
        """Create the datasource meta table"""

        self._ensure_connected()
        if self._inspect.has_table(self._meta_table_name):
            self._meta_table = Table(
                self._meta_table_name, self._orm_meta, autoload_with=self._engine
            )
            return
        table = Table(
            self._meta_table_name,
            self._orm_meta,
            Column("id", Integer, primary_key=True),
            Column("metaspec", JSON, nullable=False),
        )
        self._orm_meta.create_all(self._engine, checkfirst=True)

        self._meta_table = table

    def _create_datasource_table(self, columns: Dict[str, ColType]) -> bool:
        """Create a table in a user's datasource"""

        self._ensure_connected()
        if self._inspect.has_table(self._tablename):
            self._table = Table(
                self._tablename, self._orm_meta, autoload_with=self._engine
            )
            return False

        colspec: Dict[str, ColType] = {}
        coldef: List[Column] = []
        # we want to make sure there is an ID column specified
        if not ColType.ID in columns.values():
            colspec["id"] = ColType.INTEGER
            coldef.append(Column("id", Integer, primary_key=True))

        for colname, coltype in columns.items():
            colspec[colname] = coltype
            if coltype == ColType.ID:
                coldef.append(Column(colname, Integer, primary_key=True))
            else:
                coldef.append(Column(colname, ColTypeSQL.from_coltype(coltype).value))

        table = Table(self._tablename, self._orm_meta, *coldef)
        self._orm_meta.create_all(self._engine, checkfirst=True)

        self._table = table

        if self._colspec is None:
            self._colspec = colspec
            self._save_colspec()
        return True

    def _map_datasource_meta_table(self) -> None:
        """Map the table to the DataSourceBase"""

        self._ensure_connected()
        mapper(self.UserDataSourceMeta, self._meta_table)
        self.UserDataSourceMeta.query = self._session.query_property()

    def _map_datasource_table(self) -> None:
        """Map the table to the DataSourceBase"""

        def init_user_datasource(sub_self, row):
            """Initialize the user data source"""
            props = dir(sub_self)
            print(props)
            for col, val in row.items():
                if not col in props:
                    raise Exception(f"Column {col} not in colspec")
                setattr(sub_self, col, val)
                # sub_self.__dict__[col] = val

        self._ensure_connected()
        mapper(self.UserDataSource, self._table)
        self.UserDataSource.query = self._session.query_property()
        self.UserDataSource.row_dict = init_user_datasource

    def __del__(self):
        """Destructor"""

        self.disconnect()
