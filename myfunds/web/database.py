import peewee as pw
from flask import Flask
from flask import current_app
from flask import g

from myfunds.core.models import db_proxy


def init_database(database_path: str) -> pw.SqliteDatabase:
    return pw.SqliteDatabase(
        database_path,
        pragmas=[
            ("cache_size", -1024 * 64),
            ("journal_mode", "wal"),
            ("foreign_keys", 1),
        ],
    )


def initialize_app_database():
    g._origin_db = db_proxy.obj
    db_proxy.initialize(current_app.config["DATABASE"])


def initialize_origin_database(*_):
    db_proxy.initialize(g._origin_db)


def init_app(app: Flask) -> None:
    app.config["DATABASE"] = init_database(app.config["DATABASE_PATH"])

    app.before_request(initialize_app_database)
    app.teardown_request(initialize_origin_database)
