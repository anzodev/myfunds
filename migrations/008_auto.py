import peewee as pw


def migrate(migrator, database, fake=False, **kwargs):
    @migrator.create_model
    class TelegramBotAccount(pw.Model):
        id = pw.AutoField()
        account = pw.ForeignKeyField(
            backref="telegrambotaccount_set",
            column_name="account_id",
            field="id",
            model=migrator.orm["accounts"],
            unique=True,
        )
        chat_id = pw.IntegerField(unique=True)

        class Meta:
            table_name = "telegram_bot_accounts"


def rollback(migrator, database, fake=False, **kwargs):
    migrator.remove_model("telegram_bot_accounts")
