"""datasource: this allows a dynamic engine to be used for an individual user data source"""

import hashlib

from enum import Enum
import os
from typing import Any, Dict, List, Union

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

from sqlalchemy.engine.reflection import Inspector
from sqlalchemy.pool import NullPool
from sqlalchemy.engine import Engine
from sqlalchemy.orm import scoped_session, sessionmaker, registry


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
    def from_str(col_type: str) -> "ColType":
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
    _session_maker: Union[sessionmaker, None] = None
    _session: Union[scoped_session, None] = None
    _table: Union[Table, None] = None
    _meta_table: Union[Table, None] = None
    _colspec: Union[Dict[str, ColType], None] = None
    _text_col_name: Union[str, None] = None
    _orm_meta: MetaData
    _inspect: Union[Inspector, None] = None
    _orm_base_class: object
    _mapper_registry: registry = registry()

    _user_id: int
    _data_source_id: int
    _filename: str
    _tablename: str
    _meta_table_name: str = "datasource_meta"

    _connected: bool = False

    UserDataSourceMeta = None
    UserDataSource = None

    def _set_datasource_meta_class(self):
        if self.UserDataSourceMeta is not None:
            return
        class UserDataSourceMetaBase(self._orm_base_class): # pylint: disable=too-few-public-methods
            """UserDataSourceMeta for table spec information"""
            #__allow_unmapped__ = True
            #__abstract__ = True
            __table__  = self._meta_table

        self.UserDataSourceMeta = UserDataSourceMetaBase # pylint: disable=invalid-name

    def _set_datasource_class(self):
        if self.UserDataSource is not None:
            return
        class UserDataSourceBase(self._orm_base_class): # pylint: disable=too-few-public-methods
            """UserDataSource
            This class is for using with sqlalchemy mapper.
            It can't be declared outside this class because
            it needs to be unique per instance of DataSourceManager.
            """
            __table__  = self._table

        self.UserDataSource = UserDataSourceBase # pylint: disable=invalid-name

    def __init__(self, data_source_id: int, user_id: int) -> None:
        """Initialize the datasource manager"""

        self._data_source_id = data_source_id
        self._user_id = user_id
        self._set_base_class()
        # self._set_datasource_class()
        # self._set_datasource_meta_class()
        self._datasource_filename()

    def _set_base_class(self):
        """Set the base class for the table and meta table"""
        self._orm_base_class = self._mapper_registry.generate_base()

    def connect(self) -> None:
        """Connect to the datasource"""
        if self._engine is None:
            self._create_engine()
        self._create_session_maker()
        self._inspect = inspect(self._engine)

        self._orm_meta = self._mapper_registry.metadata
        # self._orm_meta = MetaData(self._engine)
        self._connected = True
        self._load_tables()

    def disconnect(self) -> None:
        """Disconnect from the datasource"""

        if not self._connected:
            return
        #if self._session is not None:
        #    self._session.close()
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
        else:
            self._colspec = columns

        if self.UserDataSource is None:
            self._map_datasource_table()

    def get_data_source_class(self) -> Union[None, type]:
        """Get the data source class for using with sqlalchemy"""

        self._ensure_connected()

        return self.UserDataSource

    @property
    def session(self) -> sessionmaker:
        """Get the session"""

        self._ensure_connected()

        return self._session_maker

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
        with self._session_maker() as session:
            colspec = session.query(self.UserDataSourceMeta).first()
        if colspec is not None:
            self._colspec = {}

            for colname, coltype in colspec.metaspec.items():
                self._colspec[colname] = ColType.from_str(coltype)

    def _save_colspec(self) -> None:
        """Save the column spec to the datasource meta table"""

        self._ensure_connected()

        colspec = {}
        for colname, coltype in self._colspec.items():
            colspec[colname] = coltype.value


        stmt = self._meta_table.insert().values(metaspec=colspec)
        with self._session_maker() as session:
            session.execute(stmt)
            session.commit()

    def _datasource_filename(self) -> None:
        """Get the filename for specified datasource and user"""

        ds_dir = "data/user"

        if not os.path.exists(ds_dir):
            os.makedirs(ds_dir)
        # generate a unique filename from a hash of the data source id
        # this is to prevent a user from accessing another user's data
        ds_id_hash = hashlib.sha256(str(self._data_source_id).encode()).hexdigest()
        self._tablename = f"ds_{ds_id_hash}"
        self._filename = f"{ds_dir}/user_{self._user_id}_{ds_id_hash}.db"

    def _create_engine(self) -> None:
        """Create the engine for the datasource"""

        self._engine = create_engine(
            f"sqlite:///{self._filename}",
            connect_args={"check_same_thread": False},
            poolclass=NullPool,
            future = True,
        )


    def _create_session_maker(self) -> None:
        """Create the session maker"""
        self._session_maker = sessionmaker(autocommit=False, autoflush=False, bind=self._engine)


    def _create_datasource_meta_table(self) -> None:
        """Create the datasource meta table"""

        self._ensure_connected()
        if self._inspect.has_table(self._meta_table_name, sqlite_include_internal=True):
            self._meta_table = Table(
                self._meta_table_name, self._orm_meta, autoload_with=self._engine
            )
            return
        table = Table(
            self._meta_table_name,
            self._orm_meta,
            Column("id", Integer, primary_key=True),
            Column("metaspec", JSON, nullable=False),
            extend_existing=True
        )
        self._orm_meta.create_all(self._engine, checkfirst=True)

        self._meta_table = table

    def _create_datasource_table(self, columns: Dict[str, ColType]) -> bool:
        """Create a table in a user's datasource"""

        self._ensure_connected()
        if self._inspect.has_table(self._tablename, sqlite_include_internal=True):
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
        """Map the table to the UserDataSourceMeta class"""
        if self.UserDataSourceMeta is not None:
            return
        self._ensure_connected()
        self._set_datasource_meta_class()
        # self._mapper_registry.map_imperatively(
        #     self.UserDataSourceMeta,
        #     self._meta_table)
        # self.UserDataSourceMeta.query = self._session.query_property()

    def _map_datasource_table(self) -> None:
        """Map the table to the UserDataSource"""
        if self.UserDataSource is not None:
            return

        def values_from_dict(sub_self, row: Dict[str, Any]) -> None:
            """Set the column values from a row dictionary"""

            props = dir(sub_self)

            for col, val in row.items():
                if not col in props:
                    raise Exception(f"Column {col} not in colspec")
                setattr(sub_self, col, val)

        self._ensure_connected()
        self._set_datasource_class()
        # self._mapper_registry.map_imperatively(
        #     self.UserDataSource,
        #     self._table)
        # self.UserDataSource.query = self._session.query_property()
        self.UserDataSource.values_from_dict = values_from_dict

    def __del__(self):
        """Destructor"""

        self.disconnect()
