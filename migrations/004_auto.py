def migrate(migrator, database, fake=False, **kwargs):
    migrator.add_not_null("crypto_transactions", "account")


def rollback(migrator, database, fake=False, **kwargs):
    migrator.drop_not_null("crypto_transactions", "account")
