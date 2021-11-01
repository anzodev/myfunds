import peewee as pw
from flask import Flask


def init_database(database_path: str) -> pw.SqliteDatabase:
    return pw.SqliteDatabase(
        database_path,
        pragmas=[
            ("cache_size", -1024 * 64),
            ("journal_mode", "wal"),
            ("foreign_keys", 1),
        ],
    )


def init_app(app: Flask) -> None:
    app.config["DATABASE"] = init_database(app.config["DATABASE_PATH"])
