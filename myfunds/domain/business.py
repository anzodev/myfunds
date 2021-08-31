import datetime
import inspect
from contextlib import contextmanager
from typing import List
from typing import Optional

import peewee as pw

from myfunds.tools import val

from . import models
from .constants import TransactionType


def model_list() -> List[pw.Model]:
    result = []
    for k, v in vars(models).items():
        if (
            inspect.isclass(v)
            and issubclass(v, models._BaseModel)
            and v is not models._BaseModel
        ):
            result.append(v)
    return result


def init_database(db_path: str) -> pw.SqliteDatabase:
    return pw.SqliteDatabase(
        db_path,
        pragmas=[
            ("cache_size", -1024 * 64),
            ("journal_mode", "wal"),
            ("foreign_keys", 1),
        ],
    )


@contextmanager
def database_ctx(db: pw.Database) -> None:
    origin = models.database.obj
    models.database.initialize(db)
    try:
        yield
    finally:
        models.database.initialize(origin)


def create_currency(
    code_alpha: str,
    code_num: str,
    precision: int = 100,
) -> models.Currency:
    val.verify(code_alpha, [val.is_instance(str), val.match(r"^[A-Z]{3}$")])
    val.verify(code_num, [val.is_instance(str), val.match(r"^[0-9]{3}$")])
    val.verify(precision, [val.is_instance(int)])

    return models.Currency.create(
        code_alpha=code_alpha,
        code_num=code_num,
        precision=precision,
    )


def create_account(username: str, password: str) -> models.Account:
    val.verify(username, [val.is_instance(str)])
    val.verify(len(username), [val.gt(0), val.le(80)])

    return models.Account.create(
        username=username,
        created_at=datetime.datetime.utcnow(),
    )


def create_txn_group(
    account: models.Account,
    type_: str,
    name: str,
    color_sign: str,
) -> models.TransactionGroup:
    val.verify(account, [val.is_instance(models.Account)])
    val.verify(type_, [val.in_(TransactionType)])
    val.verify(name, [val.is_instance(str)])
    val.verify(len(name), [val.gt(0), val.le(80)])
    val.verify(color_sign, [val.is_instance(str), val.match(r"^\#[0-9a-f]{6}$")])

    return models.TransactionGroup.create(
        account=account,
        type_=type_,
        name=name,
        color_sign=color_sign,
    )


def create_balance(
    account: models.Account,
    currency: models.Currency,
    name: str,
) -> models.Balance:
    val.verify(account, [val.is_instance(models.Account)])
    val.verify(currency, [val.is_instance(models.Currency)])
    val.verify(name, [val.is_instance(str)])
    val.verify(len(name), [val.gt(0)])

    return models.Balance.create(
        account=account,
        currency=currency,
        name=name,
        amount=0,
        created_at=datetime.datetime.utcnow(),
    )


def make_replenishment(
    balance: models.Balance,
    amount: int,
    txn_group: Optional[models.TransactionGroup] = None,
    comment: Optional[str] = None,
    created_at: Optional[datetime.datetime] = None,
) -> models.Transaction:
    val.verify(balance, [val.is_instance(models.Balance)])
    val.verify(amount, [val.is_instance(int), val.gt(0)])
    if txn_group is not None:
        val.verify(txn_group, [val.is_instance(models.TransactionGroup)])
        val.verify(txn_group.type_, [val.eq(TransactionType.REPLENISHMENT)])
        val.verify(txn_group.account_id, [val.eq(balance.account_id)])
    if comment is not None:
        val.verify(comment, [val.is_instance(str)])
    if created_at is not None:
        val.verify(created_at, [val.is_instance(datetime.datetime)])

    with models.database.atomic():
        created_at = created_at or datetime.datetime.utcnow()
        common_amount = 0
        balance_remainder = 0

        last_txn = (
            models.Transaction.select(models.Transaction.balance_remainder)
            .where(
                (models.Transaction.balance == balance)
                & (models.Transaction.created_at < created_at)
            )
            .order_by(models.Transaction.created_at.desc())
            .limit(1)
            .first()
        )
        if last_txn is not None:
            balance_remainder += last_txn.balance_remainder

        sametime_replenishments_sum = (
            models.Transaction.select(
                pw.fn.SUM(models.Transaction.amount).alias("value")
            )
            .where(
                (models.Transaction.balance == balance)
                & (models.Transaction.type_ == TransactionType.REPLENISHMENT)
                & (models.Transaction.created_at == created_at)
            )
            .group_by(models.Transaction.created_at)
            .first()
        )
        if sametime_replenishments_sum is not None:
            common_amount += sametime_replenishments_sum.value

        sametime_withdrawals_sum = (
            models.Transaction.select(
                pw.fn.SUM(models.Transaction.amount).alias("value")
            )
            .where(
                (models.Transaction.balance == balance)
                & (models.Transaction.type_ == TransactionType.WITHDRAWAL)
                & (models.Transaction.created_at == created_at)
            )
            .group_by(models.Transaction.created_at)
            .first()
        )
        if sametime_withdrawals_sum is not None:
            common_amount -= sametime_withdrawals_sum.value

        common_amount += amount
        balance_remainder += common_amount

        txn = models.Transaction.create(
            balance=balance,
            balance_remainder=balance_remainder,
            type_=TransactionType.REPLENISHMENT,
            group=txn_group,
            amount=amount,
            comment=comment,
            created_at=created_at,
        )

        balance.amount += amount
        balance.save(only=[models.Balance.amount])

        # fmt: off
        (
            models.Transaction
            .update(balance_remainder=balance_remainder)
            .where(
                (models.Transaction.balance == balance)
                & (models.Transaction.created_at == created_at)
            )
            .execute()
        )
        # fmt: on

        # fmt: off
        (
            models.Transaction
            .update(
                balance_remainder=(models.Transaction.balance_remainder + amount)
            )
            .where(
                (models.Transaction.balance == balance)
                & (models.Transaction.created_at > txn.created_at)
            )
            .execute()
        )
        # fmt: on

        return txn


def make_withdrawal(
    balance: models.Balance,
    amount: int,
    txn_group: Optional[models.TransactionGroup] = None,
    comment: Optional[str] = None,
    created_at: Optional[datetime.datetime] = None,
) -> models.Transaction:
    val.verify(balance, [val.is_instance(models.Balance)])
    val.verify(amount, [val.is_instance(int), val.gt(0)])
    if txn_group is not None:
        val.verify(txn_group, [val.is_instance(models.TransactionGroup)])
        val.verify(txn_group.type_, [val.eq(TransactionType.WITHDRAWAL)])
        val.verify(txn_group.account_id, [val.eq(balance.account_id)])
    if comment is not None:
        val.verify(comment, [val.is_instance(str)])
    if created_at is not None:
        val.verify(created_at, [val.is_instance(datetime.datetime)])

    with models.database.atomic():
        created_at = created_at or datetime.datetime.utcnow()
        common_amount = 0
        balance_remainder = 0

        last_txn = (
            models.Transaction.select(models.Transaction.balance_remainder)
            .where(
                (models.Transaction.balance == balance)
                & (models.Transaction.created_at < created_at)
            )
            .order_by(models.Transaction.created_at.desc())
            .limit(1)
            .first()
        )
        if last_txn is not None:
            balance_remainder += last_txn.balance_remainder

        sametime_replenishments_sum = (
            models.Transaction.select(
                pw.fn.SUM(models.Transaction.amount).alias("value")
            )
            .where(
                (models.Transaction.balance == balance)
                & (models.Transaction.type_ == TransactionType.REPLENISHMENT)
                & (models.Transaction.created_at == created_at)
            )
            .group_by(models.Transaction.created_at)
            .first()
        )
        if sametime_replenishments_sum is not None:
            common_amount += sametime_replenishments_sum.value

        sametime_withdrawals_sum = (
            models.Transaction.select(
                pw.fn.SUM(models.Transaction.amount).alias("value")
            )
            .where(
                (models.Transaction.balance == balance)
                & (models.Transaction.type_ == TransactionType.WITHDRAWAL)
                & (models.Transaction.created_at == created_at)
            )
            .group_by(models.Transaction.created_at)
            .first()
        )
        if sametime_withdrawals_sum is not None:
            common_amount -= sametime_withdrawals_sum.value

        common_amount -= amount
        balance_remainder += common_amount

        txn = models.Transaction.create(
            balance=balance,
            balance_remainder=balance_remainder,
            type_=TransactionType.WITHDRAWAL,
            group=txn_group,
            amount=amount,
            comment=comment,
            created_at=created_at,
        )

        balance.amount -= amount
        balance.save(only=[models.Balance.amount])

        # fmt: off
        (
            models.Transaction
            .update(balance_remainder=balance_remainder)
            .where(
                (models.Transaction.balance == balance)
                & (models.Transaction.created_at == created_at)
            )
            .execute()
        )
        # fmt: on

        # fmt: off
        (
            models.Transaction
            .update(
                balance_remainder=(models.Transaction.balance_remainder - amount)
            )
            .where(
                (models.Transaction.balance == balance)
                & (models.Transaction.created_at > txn.created_at)
            )
            .execute()
        )
        # fmt: on

        return txn


def rollback_transaction(txn: models.Transaction) -> None:
    val.verify(txn, [val.is_instance(models.Transaction)])
    val.verify(txn.type_, [val.in_(TransactionType)])

    balance = txn.balance

    with models.database.atomic():
        signed_amount = (
            -txn.amount if txn.type_ == TransactionType.REPLENISHMENT else txn.amount
        )

        balance.amount += signed_amount
        balance.save(only=[models.Balance.amount])

        # fmt: off
        (
            models.Transaction
            .update(
                balance_remainder=(
                    models.Transaction.balance_remainder + signed_amount
                )
            )
            .where(
                (models.Transaction.balance_id == balance.id)
                & (models.Transaction.created_at >= txn.created_at)
            )
            .execute()
        )
        # fmt: on

        txn.delete_instance()
