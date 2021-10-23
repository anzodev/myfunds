"""Peewee migrations -- 001_auto.py.

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
    class Account(pw.Model):
        id = pw.AutoField()
        username = pw.CharField(max_length=100, unique=True)
        password_hash = pw.TextField()

        class Meta:
            table_name = "accounts"

    @migrator.create_model
    class Currency(pw.Model):
        id = pw.AutoField()
        code_alpha = pw.FixedCharField(unique=True)
        precision = pw.IntegerField()

        class Meta:
            table_name = "currencies"

    @migrator.create_model
    class Balance(pw.Model):
        id = pw.AutoField()
        account = pw.ForeignKeyField(backref='balance_set', column_name='account_id', field='id', model=migrator.orm['accounts'])
        currency = pw.ForeignKeyField(backref='balance_set', column_name='currency_id', field='id', model=migrator.orm['currencies'])
        name = pw.CharField(max_length=255)
        amount = pw.IntegerField()
        created_at = pw.DateTimeField()

        class Meta:
            table_name = "balances"
            indexes = [(('account_id', 'name'), True)]

    @migrator.create_model
    class Category(pw.Model):
        id = pw.AutoField()
        account = pw.ForeignKeyField(backref='category_set', column_name='account_id', field='id', model=migrator.orm['accounts'])
        direction = pw.CharField(index=True, max_length=255)
        name = pw.CharField(max_length=255)
        color_sign = pw.CharField(max_length=255)

        class Meta:
            table_name = "categories"

    @migrator.create_model
    class BalanceLimit(pw.Model):
        id = pw.AutoField()
        balance = pw.ForeignKeyField(backref='balancelimit_set', column_name='balance_id', field='id', model=migrator.orm['balances'], on_delete='CASCADE')
        category = pw.ForeignKeyField(backref='balancelimit_set', column_name='category_id', field='id', model=migrator.orm['categories'])
        amount = pw.IntegerField()

        class Meta:
            table_name = "balance_limits"
            indexes = [(('balance_id', 'category_id'), True)]

    @migrator.create_model
    class JointLimit(pw.Model):
        id = pw.AutoField()
        currency = pw.ForeignKeyField(backref='jointlimit_set', column_name='currency_id', field='id', model=migrator.orm['currencies'])
        name = pw.CharField(max_length=255, unique=True)
        amount = pw.IntegerField()

        class Meta:
            table_name = "joint_limits"

    @migrator.create_model
    class JointLimitParticipant(pw.Model):
        id = pw.AutoField()
        limit = pw.ForeignKeyField(backref='jointlimitparticipant_set', column_name='limit_id', field='id', model=migrator.orm['joint_limits'], on_delete='CASCADE')
        category = pw.ForeignKeyField(backref='jointlimitparticipant_set', column_name='category_id', field='id', model=migrator.orm['categories'])

        class Meta:
            table_name = "joint_limit_participants"
            indexes = [(('limit_id', 'category_id'), True)]

    @migrator.create_model
    class Transaction(pw.Model):
        id = pw.AutoField()
        balance = pw.ForeignKeyField(backref='transaction_set', column_name='balance_id', field='id', model=migrator.orm['balances'], on_delete='CASCADE')
        balance_remainder = pw.IntegerField()
        direction = pw.CharField(index=True, max_length=255)
        category = pw.ForeignKeyField(backref='transaction_set', column_name='category_id', field='id', model=migrator.orm['categories'], null=True, on_delete='SET NULL')
        amount = pw.IntegerField()
        comment = pw.TextField(null=True)
        created_at = pw.DateTimeField(index=True)

        class Meta:
            table_name = "transactions"



def rollback(migrator, database, fake=False, **kwargs):
    """Write your rollback migrations here."""

    migrator.remove_model('transactions')

    migrator.remove_model('joint_limit_participants')

    migrator.remove_model('joint_limits')

    migrator.remove_model('balance_limits')

    migrator.remove_model('categories')

    migrator.remove_model('balances')

    migrator.remove_model('currencies')

    migrator.remove_model('accounts')
