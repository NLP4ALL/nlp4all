"""datasource: this allows a dynamic engine to be used for an individual user data source"""

import os
import hashlib
# from greenlet import getcurrent
import sqlalchemy
from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base

DataSourceBase = declarative_base()

def get_session(data_source_id: str, user_id: int) -> scoped_session:
    """Get the engine for the current user"""

    # generate a unique filename from a hash of the data source id
    # this is to prevent a user from accessing another user's data
    filename = hashlib.sha256(data_source_id.encode()).hexdigest()

    engine = create_engine(
        f'sqlite:///data/user_{user_id}_{filename}.db',
        connect_args={"check_same_thread": False})

    db_session = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))
    # bind=engine,
    # scopefunc=getcurrent))
    # Base.query = db_session.query_property()
    return db_session


class DataSource(DataSourceBase): # pylint: disable=too-few-public-methods
    """Dynamic SqlAlchemy table in a database file
    Users can have their own columns and values, only requiring a unique data source id
    """

    __tablename__ = 'data_source'

    id = Column(Integer, primary_key=True)
    data_source_id = Column(String(80), unique=True, nullable=False)
    user_id = Column(Integer, nullable=False)

    def __init__(self, data_source_id: str, user_id: int):
        self.data_source_id = data_source_id
        self.user_id = user_id

    def __repr__(self):
        return f'<DataSource {self.data_source_id} {self.user_id}>'

def create_data_source(data_source_id: str, user_id: int):
    """Create a new data source for the current user"""

    # create the database file
    session = get_session(data_source_id, user_id)
    DataSourceBase.metadata.create_all(session.bind)

    # add the data source to the data_source table
    data_source = DataSource(data_source_id, user_id)
    session.add(data_source)
    session.commit()

def get_data_source(data_source_id: str, user_id: int):
    """Get the data source for the current user"""

    session = get_session(data_source_id, user_id)
    data_source = session.query(DataSource).filter_by(
        data_source_id=data_source_id,
        user_id=user_id).first()
    return data_source

def delete_data_source(data_source_id: str, user_id: int):
    """Delete the data source for the current user"""

    session = get_session(data_source_id, user_id)
    data_source = session.query(DataSource).filter_by(
        data_source_id=data_source_id,
        user_id=user_id).first()
    session.delete(data_source)
    session.commit()

    # delete the database file
    filename = hashlib.sha256(data_source_id.encode()).hexdigest()
    os.remove(f'data/user_{user_id}_{filename}.db')

def get_data_source_columns(data_source_id: str, user_id: int):
    """Get the columns for the current user"""

    session = get_session(data_source_id, user_id)
    data_source = session.query(DataSource).filter_by(
        data_source_id=data_source_id,
        user_id=user_id).first()
    return data_source.__table__.columns

def add_data_source_column(
                data_source_id: str,
                user_id: int,
                column_name: str,
                column_type: sqlalchemy.types.TypeEngine):
    """Add a column to the current user's data source"""

    session = get_session(data_source_id, user_id)
    data_source = session.query(DataSource).filter_by(
        data_source_id=data_source_id,
        user_id=user_id).first()
    column = Column(column_name, column_type)
    column.create(data_source.__table__)
    session.commit()
