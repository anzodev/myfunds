import datetime
import time
from typing import Optional

import peewee as pw
import pytest

from myfunds.domain import models
from myfunds.domain.constants import TransactionType


@pytest.fixture
def models_defaults():
    dt = datetime.datetime(2021, 1, 1, 12, 24, 48)
    return {
        "currency": {
            "code_num": "840",
            "code_alpha": "USD",
            "base": 10,
        },
        "account": {
            "username": "developer",
            "created_at": dt,
        },
        "balance": {
            "name": "personal",
            "amount": 0,
            "created_at": dt,
        },
        "txn_group": {
            "name": "transfer",
            "color_sign": "#d9534f",
        },
        "txn": {
            "balance_remainder": 1025,
            "amount": 1025,
            "comment": "transfer to card 4444111122223333",
            "created_at": dt,
        },
        "plan": {
            "name": "new pc",
            "description": "new pc with top config",
            "target_amount": 250000,
            "target_date": dt + datetime.timedelta(days=20),
            "created_at": dt,
        },
    }


@pytest.fixture
def new_currency(models_defaults):
    def _new_currency(
        code_num: Optional[str] = None,
        code_alpha: Optional[str] = None,
        base: Optional[int] = None,
    ):
        defaults = models_defaults["currency"]
        return models.Currency.create(
            code_num=code_num or defaults["code_num"],
            code_alpha=code_alpha or defaults["code_alpha"],
            base=base or defaults["base"],
        )

    return _new_currency


@pytest.fixture
def new_account(models_defaults):
    def _new_account(
        username: Optional[str] = None, created_at: Optional[datetime.datetime] = None
    ):
        defaults = models_defaults["account"]
        return models.Account.create(
            username=username or defaults["username"],
            password_hash="0000",
            created_at=created_at or defaults["created_at"],
        )

    return _new_account


@pytest.fixture
def new_balance(models_defaults):
    def _new_balance(
        account: models.Account,
        currency: models.Currency,
        name: Optional[str] = None,
        amount: Optional[int] = None,
        created_at: Optional[datetime.datetime] = None,
    ):
        defaults = models_defaults["balance"]
        return models.Balance.create(
            account=account,
            currency=currency,
            name=name or defaults["name"],
            amount=amount or defaults["amount"],
            created_at=created_at or defaults["created_at"],
        )

    return _new_balance


@pytest.fixture
def _create_txn_group(models_defaults):
    def __create_txn_group(
        type_: str,
        account: models.Account,
        name: Optional[str] = None,
        color_sign: Optional[str] = None,
    ):
        defaults = models_defaults["txn_group"]
        return models.TransactionGroup.create(
            account=account,
            type_=type_,
            name=name or defaults["name"],
            color_sign=color_sign or defaults["color_sign"],
        )

    return __create_txn_group


@pytest.fixture
def new_replenishment_group(_create_txn_group):
    def _new_replenishment_group(**kwargs):
        return _create_txn_group(TransactionType.REPLENISHMENT, **kwargs)

    return _new_replenishment_group


@pytest.fixture
def new_withdrawal_group(_create_txn_group):
    def _new_withdrawal_group(**kwargs):
        return _create_txn_group(TransactionType.WITHDRAWAL, **kwargs)

    return _new_withdrawal_group


@pytest.fixture
def _create_txn(models_defaults):
    def __create_txn(
        type_: str,
        balance: models.Balance,
        id_: Optional[int] = None,
        balance_remainder: Optional[int] = None,
        group: Optional[models.TransactionGroup] = None,
        amount: Optional[int] = None,
        comment: Optional[str] = None,
        created_at: Optional[datetime.datetime] = None,
    ):
        defaults = models_defaults["txn"]
        kwargs = {
            "balance": balance,
            "balance_remainder": balance_remainder or defaults["balance_remainder"],
            "type_": type_,
            "group": group,
            "amount": amount or defaults["amount"],
            "comment": comment or defaults["comment"],
            "created_at": created_at or defaults["created_at"],
        }
        if id_ is not None:
            kwargs["id"] = id_
        return models.Transaction.create(**kwargs)

    return __create_txn


@pytest.fixture
def new_replenishment(_create_txn):
    def _new_replenishment(**kwargs):
        return _create_txn(TransactionType.REPLENISHMENT, **kwargs)

    return _new_replenishment


@pytest.fixture
def new_withdrawal(_create_txn):
    def _new_withdrawal(**kwargs):
        return _create_txn(TransactionType.WITHDRAWAL, **kwargs)

    return _new_withdrawal


@pytest.fixture
def new_plan(models_defaults):
    def _new_plan(
        account: models.Account,
        balance: models.Balance,
        name: Optional[str] = None,
        description: Optional[str] = None,
        target_amount: Optional[int] = None,
        target_date: Optional[datetime.datetime] = None,
        created_at: Optional[datetime.datetime] = None,
    ):
        defaults = models_defaults["plan"]
        return models.Plan.create(
            account=account,
            balance=balance,
            name=name or defaults["name"],
            description=description or defaults["description"],
            target_amount=target_amount or defaults["target_amount"],
            target_date=target_date or defaults["target_date"],
            created_at=created_at or defaults["created_at"],
        )

    return _new_plan


# ---


@pytest.fixture(scope="module", autouse=True)
def _init_database():
    database = pw.SqliteDatabase(":memory:", pragmas=[("foreign_keys", 1)])
    models.database.initialize(database)
    models.database.create_tables(
        [
            models.Currency,
            models.Account,
            models.Balance,
            models.TransactionGroup,
            models.Transaction,
            models.Plan,
        ]
    )
    return database


@pytest.fixture
def db_transaction_ctx():
    with models.database.transaction() as txn:
        yield
        txn.rollback()


@pytest.fixture
def execution_timing():
    def _execution_timing(f):
        def wrapper(*args, **kwargs):
            t0 = time.time()
            result = f(*args, **kwargs)
            t1 = time.time()
            return t0, t1, result

        return wrapper

    return _execution_timing
