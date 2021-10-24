"""Peewee migrations -- 002_auto.py.

Some examples (model - class or model name)::

    > Model = migrator.orm['model_name']            # Return model in current state by name

    > migrator.sql(sql)                             # Run custom SQL
    > migrator.python(func, *args, **kwargs)        # Run python code
    > migrator.create_model(Model)                  # Create a model (could be used as decorator)
    > migrator.remove_model(model, cascade=True)    # Remove a model
    > migrator.add_fields(model, **fields)          # Add fields to a model
    > migrator.change_fields(model, **fields)       # Change fields
    > migrator.remove_fields(model, *field_names, cascade=True)
    > migrator.rename_field(model, old_field_name, new_field_name)
    > migrator.rename_table(model, new_table_name)
    > migrator.add_index(model, *col_names, unique=False)
    > migrator.drop_index(model, *col_names)
    > migrator.add_not_null(model, *field_names)
    > migrator.drop_not_null(model, *field_names)
    > migrator.add_default(model, field_name, default)

"""

import datetime as dt
import peewee as pw
from decimal import ROUND_HALF_EVEN

try:
    import playhouse.postgres_ext as pw_pext
except ImportError:
    pass

SQL = pw.SQL


def migrate(migrator, database, fake=False, **kwargs):
    """Write your migrations here."""

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
        account = pw.ForeignKeyField(backref='cryptobalance_set', column_name='account_id', field='id', model=migrator.orm['accounts'])
        currency = pw.ForeignKeyField(backref='cryptobalance_set', column_name='currency_id', field='id', model=migrator.orm['crypto_currencies'])
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
    """Write your rollback migrations here."""

    migrator.remove_model('crypto_currencies')

    migrator.remove_model('crypto_balances')

    migrator.remove_model('crypto_action_logs')

    migrator.remove_model('crypto_transactions')
