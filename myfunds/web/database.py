import peewee as pw


def init_database(db_path: str) -> pw.SqliteDatabase:
    return pw.SqliteDatabase(
        db_path,
        pragmas=[
            ("cache_size", -1024 * 64),
            ("journal_mode", "wal"),
            ("foreign_keys", 1),
        ],
    )
