import secrets
from contextlib import contextmanager
from datetime import datetime
from typing import Optional

import peewee as pw
import pytest

from myfunds.core.constants import FundsDirection
from myfunds.core.models import Account
from myfunds.core.models import Balance
from myfunds.core.models import Category
from myfunds.core.models import Currency
from myfunds.core.models import Transaction
from myfunds.core.models import db_proxy
from myfunds.core.models import get_models


@pytest.fixture
def make_currency():
    def _make_currency(code_alpha: str = "USD", precision: int = 2):
        return Currency.create(code_alpha=code_alpha, precision=precision)

    return _make_currency


@pytest.fixture
def make_account():
    def _make_account(username: Optional[str] = None):
        username = f"john_doe_{secrets.token_hex(8)}" if username is None else username
        return Account.create(username=username, password_hash="********")

    return _make_account


@pytest.fixture
def make_balance(make_account, make_currency):
    def _make_balance(
        account: Optional[Account] = None,
        currency: Optional[Currency] = None,
        name: Optional[str] = None,
        amount: int = 0,
        created_at: Optional[datetime] = None,
    ):
        return Balance.create(
            account=(make_account() if account is None else account),
            currency=(
                (Currency.get_or_none(code_alpha="USD") or make_currency())
                if currency is None
                else currency
            ),
            name=(f"test_balance_{secrets.token_hex(8)}" if name is None else name),
            amount=amount,
            created_at=(created_at or datetime.now()),
        )

    return _make_balance


@pytest.fixture
def make_category(make_account):
    def _make_category(
        direction: str,
        account: Optional[Account] = None,
        name: str = "test_category",
        color_sign: str = "#000000",
    ):
        return Category.create(
            account=(make_account() if account is None else account),
            direction=direction,
            name=name,
            color_sign=color_sign,
        )

    return _make_category


@pytest.fixture
def make_income_category(make_category):
    def _make_income_category(**kwargs):
        return make_category(FundsDirection.INCOME, **kwargs)

    return _make_income_category


@pytest.fixture
def make_expense_category(make_category):
    def _make_expense_category(**kwargs):
        return make_category(FundsDirection.EXPENSE, **kwargs)

    return _make_expense_category


@pytest.fixture
def make_txn(make_balance):
    def _make_txn(
        direction: str,
        balance: Optional[Balance] = None,
        balance_remainder: int = 100,
        category: Optional[Category] = None,
        amount: int = 100,
        comment: Optional[str] = None,
        created_at: Optional[datetime] = None,
    ):
        return Transaction.create(
            balance=(make_balance if balance is None else balance),
            balance_remainder=balance_remainder,
            direction=direction,
            category=category,
            amount=amount,
            comment=comment,
            created_at=(created_at or datetime.now()),
        )

    return _make_txn


@pytest.fixture
def make_replenishment(make_txn):
    def _make_replenishment(**kwargs):
        return make_txn(FundsDirection.INCOME, **kwargs)

    return _make_replenishment


@pytest.fixture
def make_withdrawal(make_txn):
    def _make_withdrawal(**kwargs):
        return make_txn(FundsDirection.EXPENSE, **kwargs)

    return _make_withdrawal


@pytest.fixture
def models_db_init_context():
    @contextmanager
    def _models_db_init_context(db: pw.Database):
        origin_db = db_proxy.obj
        db_proxy.initialize(db)
        try:
            yield
        finally:
            db_proxy.initialize(origin_db)

    return _models_db_init_context


@pytest.fixture
def with_memory_database(models_db_init_context):
    db = pw.SqliteDatabase(":memory:")
    with models_db_init_context(db):
        db.create_tables(get_models())
        yield
