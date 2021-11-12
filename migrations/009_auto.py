import peewee as pw


try:
    import playhouse.sqlite_ext as pw_pext
except ImportError:
    pass


def migrate(migrator, database, fake=False, **kwargs):
    @migrator.create_model
    class TransactionImportSettings(pw.Model):
        id = pw.AutoField()
        balance = pw.ForeignKeyField(
            backref="transactionimportsettings_set",
            column_name="balance_id",
            field="id",
            model=migrator.orm["balances"],
            unique=True,
        )
        provider = pw.CharField(max_length=255)
        config = pw_pext.JSONField()
        internal_data = pw_pext.JSONField()

        class Meta:
            table_name = "transaction_import_settings"


def rollback(migrator, database, fake=False, **kwargs):
    migrator.remove_model("transaction_import_settings")
