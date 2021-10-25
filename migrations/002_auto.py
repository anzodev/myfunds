import peewee as pw


def migrate(migrator, database, fake=False, **kwargs):
    @migrator.create_model
    class CryptoCurrency(pw.Model):
        id = pw.AutoField()
        symbol = pw.CharField(max_length=255, unique=True)
        name = pw.CharField(max_length=255)
        cmc_id = pw.IntegerField()
        icon = pw.TextField()

        class Meta:
            table_name = "crypto_currencies"

    @migrator.create_model
    class CryptoBalance(pw.Model):
        id = pw.AutoField()
        account = pw.ForeignKeyField(
            backref="cryptobalance_set",
            column_name="account_id",
            field="id",
            model=migrator.orm["accounts"],
        )
        currency = pw.ForeignKeyField(
            backref="cryptobalance_set",
            column_name="currency_id",
            field="id",
            model=migrator.orm["crypto_currencies"],
        )
        name = pw.CharField(max_length=255)
        quantity = pw.IntegerField()

        class Meta:
            table_name = "crypto_balances"

    @migrator.create_model
    class CryptoActionLog(pw.Model):
        id = pw.AutoField()
        message = pw.TextField()
        created_at = pw.DateTimeField(index=True)

        class Meta:
            table_name = "crypto_action_logs"

    @migrator.create_model
    class CryptoTransaction(pw.Model):
        id = pw.AutoField()
        direction = pw.CharField(index=True, max_length=255)
        symbol = pw.CharField(max_length=255)
        quantity = pw.IntegerField()
        price = pw.IntegerField()
        amount = pw.IntegerField()
        created_at = pw.DateTimeField(index=True)

        class Meta:
            table_name = "crypto_transactions"


def rollback(migrator, database, fake=False, **kwargs):
    migrator.remove_model("crypto_transactions")

    migrator.remove_model("crypto_action_logs")

    migrator.remove_model("crypto_balances")

    migrator.remove_model("crypto_currencies")
