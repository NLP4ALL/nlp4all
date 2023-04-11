"""Mongo Flask Plugin"""

import typing as t
from pymongo import MongoClient, ASCENDING, TEXT
from pymongo.collection import Collection
from pymongo.database import Database
from flask import Flask
from ..config import MONGODB_HOST, MONGO_INITDB_ROOT_PASSWORD, MONGO_INITDB_ROOT_USERNAME


class Mongo:
    """"Mongo Flask Plugin"""

    _conn: t.Union[MongoClient, None]
    app: t.Union[Flask, None]
    _db: t.Union[Database, None]

    def __init__(self, app: t.Optional[Flask] = None):
        if app is not None:
            self.init_app(app)

    def init_app(self, app: Flask) -> None:
        """Initialize the app."""
        self.app = app
        CONNECTION_STRING = f"mongodb://{MONGO_INITDB_ROOT_USERNAME}:{MONGO_INITDB_ROOT_PASSWORD}@{MONGODB_HOST}"
        CONNECTION_STRING = CONNECTION_STRING + ":27017/nlp4all?authSource=admin"
        app.logger.info("Connecting to MongoDB: %s", CONNECTION_STRING)
        self._conn = MongoClient(CONNECTION_STRING)
        self._db = self._conn.get_database()
        app.extensions["mongo"] = self

    def get_conn(self) -> t.Union[MongoClient, None]:
        """Get the connection."""
        return self._conn

    def get_collection(self, collection_name: str) -> Collection:
        """Get the collection."""
        if self._db is None:
            raise RuntimeError("Database not initialized")
        return self._db.get_collection(collection_name)

    def add_indices_to_collection(
            self,
            collection: t.Union[str, Collection],
            index_paths: t.Dict[str, t.Tuple[str, ...]],
            primary_text_field: str) -> None:
        """Add index to collection."""
        if self._db is None:
            raise RuntimeError("Database not initialized")
        if isinstance(collection, str):
            collection = self._db.get_collection(collection)
        for index_path, tipe in index_paths.items():
            if tipe[0] in ("number", "integer", "boolean"):
                if self.app:
                    self.app.logger.info("Creating index %s", index_path)
                collection.create_index([(index_path, ASCENDING)], background=True)
            elif index_path == primary_text_field and tipe[0] == "string":
                if self.app:
                    self.app.logger.info("Creating MAIN TEXT index %s", index_path)
                collection.create_index([(index_path, TEXT)], background=True)
            collection.create_index(index_path)
