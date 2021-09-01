import inspect

import peewee as pw

from myfunds.core.constants import FundsDirection


db_proxy = pw.DatabaseProxy()


class BaseModel(pw.Model):
    class Meta:
        database = db_proxy


class Currency(BaseModel):
    class Meta:
        table_name = "currencies"

    code_alpha = pw.FixedCharField(max_length=3, unique=True)
    precision = pw.IntegerField()


class Account(BaseModel):
    class Meta:
        table_name = "accounts"

    username = pw.CharField(max_length=100, unique=True)
    password_hash = pw.TextField()


class Balance(BaseModel):
    class Meta:
        table_name = "balances"
        indexes = ((("account_id", "name"), True),)

    account = pw.ForeignKeyField(Account)
    currency = pw.ForeignKeyField(Currency)
    name = pw.CharField()
    amount = pw.IntegerField()
    created_at = pw.DateTimeField()


class Category(BaseModel):
    class Meta:
        table_name = "categories"

    account = pw.ForeignKeyField(Account)
    direction = pw.CharField(
        index=True, choices=[FundsDirection.EXPENSE, FundsDirection.INCOME]
    )
    name = pw.CharField()
    color_sign = pw.CharField()


class CategoryMonthLimit(BaseModel):
    class Meta:
        table_name = "category_month_limits"
        indexes = ((("balance_id", "category_id"), True),)

    balance = pw.ForeignKeyField(Balance)
    category = pw.ForeignKeyField(Category)
    amount_limit = pw.IntegerField()


class Transaction(BaseModel):
    class Meta:
        table_name = "transactions"

    balance = pw.ForeignKeyField(Balance, on_delete="CASCADE")
    balance_remainder = pw.IntegerField()
    direction = pw.CharField(
        index=True, choices=[FundsDirection.EXPENSE, FundsDirection.INCOME]
    )
    category = pw.ForeignKeyField(Category, null=True, on_delete="SET NULL")
    amount = pw.IntegerField()
    comment = pw.TextField(null=True)
    created_at = pw.DateTimeField(index=True)


def get_models() -> list[BaseModel]:
    # fmt: off
    return [
        i for i in globals().values()
        if (inspect.isclass(i) and issubclass(i, BaseModel))
    ]
    # fmt: on