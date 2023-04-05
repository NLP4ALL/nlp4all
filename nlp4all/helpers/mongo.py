"""Mongo Flask Plugin"""

import typing as t
from pymongo import MongoClient
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
        CONNECTION_STRING = f"mongodb://{MONGO_INITDB_ROOT_USERNAME}:{MONGO_INITDB_ROOT_PASSWORD}@{MONGODB_HOST}:27017/nlp4all?authSource=admin"
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
