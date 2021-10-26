import peewee as pw


def migrate(migrator, database, fake=False, **kwargs):
    migrator.add_fields(
        "crypto_transactions",
        account=pw.ForeignKeyField(
            backref="cryptotransaction_set",
            column_name="account_id",
            field="id",
            model=migrator.orm["accounts"],
            null=True,
        ),
    )


def rollback(migrator, database, fake=False, **kwargs):
    migrator.remove_fields("crypto_transactions", "account")
