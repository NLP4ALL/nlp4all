# pylint: disable=invalid-name
"""DataSource.py: Data source model

This will be use to interface with individual users' data sources
"""

from typing import Union, Dict
from sqlalchemy import Column, Integer, String, ForeignKey, inspect
from sqlalchemy import event

from .database import Base
from .datasource_manager import DataSourceManager, ColType

class DataSource(Base): # pylint: disable=too-few-public-methods
    """DataSource class manages users' data sources"""

    __tablename__ = 'data_source'

    id = Column(Integer, primary_key=True)
    user = Column(Integer, ForeignKey("user.id"), nullable=False)
    data_source_name = Column(String(80), nullable=False)
    data = Column()

    _dsm: Union[DataSourceManager, None] = None

    def load(self) -> None:
        """Load data source"""
        insp = inspect(self)
        if not insp.has_identity:
            raise ValueError("Data source not saved yet")

        if self._dsm is None:
            self._dsm = DataSourceManager(self.id, self.user)

    def unload(self) -> None:
        """Unload data source"""
        if self._dsm is not None:
            self._dsm.disconnect()
            self._dsm = None

    def create(self, columns: Dict[str, ColType]) -> None:
        """Create a new data source"""
        if self._dsm is None:
            self.load()
        if not self._dsm.is_connected():
            self._dsm.connect()
        self._dsm.create_table(columns)

    def data_source_manager(self) -> DataSourceManager:
        """Return data source manager"""
        if self._dsm is None:
            self.load()

        if not self._dsm.is_connected():
            self._dsm.connect()

        return self._dsm

    def delete_data_source(self) -> None:
        """This will delete the data source file"""
        if self._dsm is None:
            self.load()
        self._dsm.delete_data_source()
        self._dsm = None

@event.listens_for(DataSource, 'after_delete')
def after_delete_data_source(mapper, connection, target): # pylint: disable=unused-argument
    """
    After delete user event.
    This deletes the data source file when the DataSource is deleted
    """
    target.delete_data_source()
