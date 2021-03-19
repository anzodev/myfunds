import peewee as pw


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

    def amount_repr(self) -> str:
        base = self.currency.base
        return f"{self.amount / (10 ** base):.{base}f}"


class TransactionGroup(_BaseModel):
    class Meta:
        table_name = "transaction_groups"

    account = pw.ForeignKeyField(Account)
    type_ = pw.CharField(column_name="type", index=True)
    name = pw.CharField()
    color_sign = pw.CharField()


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
        base = self.balance.currency.base
        return f"{self.amount / (10 ** base):.{base}f}"

    def balance_remainder_repr(self) -> str:
        base = self.balance.currency.base
        return f"{self.balance_remainder / (10 ** base):.{base}f}"


class Plan(_BaseModel):
    class Meta:
        table_name = "plans"

    account = pw.ForeignKeyField(Account)
    balance = pw.ForeignKeyField(Balance, on_delete="CASCADE")
    name = pw.CharField()
    description = pw.TextField(null=True)
    target_amount = pw.IntegerField()
    target_date = pw.DateTimeField()
    created_at = pw.DateTimeField()
