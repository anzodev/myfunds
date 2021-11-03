import peewee as pw


def init_database(database_path: str) -> pw.SqliteDatabase:
    return pw.SqliteDatabase(
        database_path,
        pragmas=[
            ("cache_size", -1024 * 64),
            ("journal_mode", "wal"),
            ("foreign_keys", 1),
        ],
    )
