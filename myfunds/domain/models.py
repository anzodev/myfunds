import peewee as pw
from playhouse.sqlite_ext import JSONField


database = pw.DatabaseProxy()


class _BaseModel(pw.Model):
    class Meta:
        database = database


class Currency(_BaseModel):
    class Meta:
        table_name = "currencies"

    code_alpha = pw.FixedCharField(max_length=3, unique=True)
    code_num = pw.FixedCharField(max_length=3, unique=True)
    base = pw.IntegerField()


class Account(_BaseModel):
    class Meta:
        table_name = "accounts"

    username = pw.CharField(unique=True, max_length=80)
    password_hash = pw.TextField()
    ip_whitelist = JSONField(default=list)
    created_at = pw.DateTimeField()


class Balance(_BaseModel):
    class Meta:
        table_name = "balances"
        indexes = ((("account_id", "name"), True),)

    account = pw.ForeignKeyField(Account)
    currency = pw.ForeignKeyField(Currency)
    name = pw.CharField()
    amount = pw.IntegerField()
    created_at = pw.DateTimeField()

    def to_amount_repr(self, value: int) -> str:
        base = self.currency.base
        return f"{value / (10 ** base):.{base}f}"

    def amount_repr(self) -> str:
        return self.to_amount_repr(self.amount)


class TransactionGroup(_BaseModel):
    class Meta:
        table_name = "transaction_groups"

    account = pw.ForeignKeyField(Account)
    type_ = pw.CharField(column_name="type", index=True)
    name = pw.CharField()
    color_sign = pw.CharField()


class TransactionGroupLimit(_BaseModel):
    class Meta:
        table_name = "transaction_group_limits"
        indexes = ((("balance_id", "group_id"), True),)

    balance = pw.ForeignKeyField(Balance)
    group = pw.ForeignKeyField(TransactionGroup)
    month_limit = pw.IntegerField()

    def month_limit_repr(self) -> str:
        return self.balance.to_amount_repr(self.month_limit)


class Transaction(_BaseModel):
    class Meta:
        table_name = "transactions"

    balance = pw.ForeignKeyField(Balance, on_delete="CASCADE")
    balance_remainder = pw.IntegerField()
    type_ = pw.CharField(column_name="type", index=True)
    group = pw.ForeignKeyField(TransactionGroup, on_delete="SET NULL", null=True)
    amount = pw.IntegerField()
    comment = pw.TextField(null=True)
    created_at = pw.DateTimeField(index=True)

    def amount_repr(self) -> str:
        return self.balance.to_amount_repr(self.amount)

    def balance_remainder_repr(self) -> str:
        return self.balance.to_amount_repr(self.balance_remainder)


class CryptoBalance(_BaseModel):
    class Meta:
        table_name = "crypto_balances"
        indexes = ((("account_id", "name"), True),)

    account = pw.ForeignKeyField(Account)
    name = pw.CharField()
    symbol = pw.CharField()
    cmc_symbol_id = pw.IntegerField(null=True)
    amount = pw.IntegerField(default=0)
    amount_usd = pw.IntegerField(null=True)
    price = pw.IntegerField(null=True, default=0)
    created_at = pw.DateTimeField()

    def amount_repr(self) -> str:
        return f"{self.amount / (10 ** 8):.8f}"

    def amount_usd_repr(self) -> str:
        if self.amount_usd is None:
            return "0.00"
        return f"{self.amount_usd / (10 ** 2):.2f}"

    def price_repr(self) -> str:
        if self.price is None:
            return "0.00"
        return f"{self.price / (10 ** 2):.2f}"
