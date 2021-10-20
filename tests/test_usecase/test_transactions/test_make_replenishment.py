from datetime import datetime
from datetime import timedelta

import pytest

from myfunds.core import models
from myfunds.core.constants import FundsDirection
from myfunds.core.usecase import transactions as txn_usecase
from myfunds.modules import check


@pytest.mark.usefixtures("with_memory_database")
@pytest.mark.freeze_time("2021-01-01 15:30:45")
def test_call_with_default_params(make_balance):
    balance = make_balance()

    txn = txn_usecase.make_replenishment(balance=balance, amount=100)

    assert txn.balance == balance
    assert txn.balance_remainder == 100
    assert txn.direction == FundsDirection.INCOME
    assert txn.category is None
    assert txn.amount == 100
    assert txn.comment is None
    assert txn.created_at == datetime(2021, 1, 1, 15, 30, 45)


@pytest.mark.usefixtures("with_memory_database")
@pytest.mark.freeze_time("2021-01-01 15:30:45")
def test_call_with_full_params(make_account, make_balance, make_income_category):
    account = make_account()
    balance = make_balance(account=account)
    category = make_income_category(account=account)
    comment = "test replenishment"
    created_at = datetime.now()

    txn = txn_usecase.make_replenishment(
        balance=balance,
        amount=100,
        category=category,
        comment=comment,
        created_at=created_at,
    )

    assert txn.balance == balance
    assert txn.balance_remainder == 100
    assert txn.direction == FundsDirection.INCOME
    assert txn.category == category
    assert txn.amount == 100
    assert txn.comment == comment
    assert txn.created_at == created_at


@pytest.mark.usefixtures("with_memory_database")
def test_balance_value_checking(make_account):
    account = make_account()

    with pytest.raises(check.ValidationError):
        txn_usecase.make_replenishment(balance=account, amount=100)


@pytest.mark.usefixtures("with_memory_database")
def test_amount_value_checking(make_account, make_currency, make_balance):
    balance = make_balance(make_account(), make_currency())

    with pytest.raises(check.ValidationError):
        txn_usecase.make_replenishment(balance=balance, amount=0)
        txn_usecase.make_replenishment(balance=balance, amount=-1)
        txn_usecase.make_replenishment(balance=balance, amount=0.5)


@pytest.mark.usefixtures("with_memory_database")
def test_category_value_checking(
    make_account, make_balance, make_income_category, make_expense_category
):
    account1 = make_account()
    account2 = make_account()
    balance1 = make_balance(account=account1)
    balance2 = make_balance(account=account2)
    category1 = make_income_category(account=account1)
    category2 = make_income_category(account=account2)

    with pytest.raises(check.ValidationError):
        txn_usecase.make_replenishment(balance=balance1, amount=1, category=balance1)
        txn_usecase.make_replenishment(
            balance=balance1,
            amount=1,
            category=make_expense_category(account=account1),
        )
        txn_usecase.make_replenishment(balance=balance1, amount=1, category=category2)
        txn_usecase.make_replenishment(balance=balance2, amount=1, category=category1)


@pytest.mark.usefixtures("with_memory_database")
def test_comment_value_checking(make_balance):
    balance = make_balance()

    with pytest.raises(check.ValidationError):
        txn_usecase.make_replenishment(balance=balance, amount=1, comment=0)


@pytest.mark.usefixtures("with_memory_database")
def test_created_at_value_checking(make_balance):
    balance = make_balance()

    with pytest.raises(check.ValidationError):
        txn_usecase.make_replenishment(balance=balance, amount=1, created_at=0)


@pytest.mark.usefixtures("with_memory_database")
def test_first_txn_calculation(make_balance):
    balance = make_balance()

    txn = txn_usecase.make_replenishment(balance=balance, amount=2050)
    assert txn.balance_remainder == 2050
    assert txn.amount == 2050
    assert models.Balance.get().amount == 2050


@pytest.mark.usefixtures("with_memory_database")
def test_second_txn_calculation(make_balance):
    balance = make_balance()

    txn0 = txn_usecase.make_replenishment(balance=balance, amount=1050)
    assert txn0.balance_remainder == 1050
    assert txn0.amount == 1050
    assert models.Balance.get().amount == 1050

    txn1 = txn_usecase.make_replenishment(balance=balance, amount=2025)
    assert txn1.balance_remainder == 3075
    assert txn1.amount == 2025
    assert models.Balance.get().amount == 3075


@pytest.mark.usefixtures("with_memory_database")
def test_sametime_created_txn_calculation(make_balance):
    balance = make_balance()

    now = datetime.now()
    one_minute_ago = now - timedelta(minutes=1)

    txn0 = txn_usecase.make_replenishment(
        balance=balance, amount=1050, created_at=one_minute_ago
    )
    assert txn0.balance_remainder == 1050
    assert txn0.amount == 1050
    assert models.Balance.get().amount == 1050

    txn1 = txn_usecase.make_replenishment(balance=balance, amount=2025, created_at=now)
    assert txn1.balance_remainder == 3075
    assert txn1.amount == 2025
    assert models.Balance.get().amount == 3075

    txn2 = txn_usecase.make_replenishment(balance=balance, amount=500, created_at=now)
    assert txn2.balance_remainder == 3575
    assert txn2.amount == 500
    assert models.Balance.get().amount == 3575

    assert models.Transaction.get(id=txn0.id).balance_remainder == 1050
    assert models.Transaction.get(id=txn0.id).amount == 1050

    assert models.Transaction.get(id=txn1.id).balance_remainder == 3575
    assert models.Transaction.get(id=txn1.id).amount == 2025


@pytest.mark.usefixtures("with_memory_database")
def test_txn_calculation_between_txns(make_balance):
    balance = make_balance()

    now = datetime.now()
    one_minute_ago = now - timedelta(minutes=1)
    after_one_minute = now + timedelta(minutes=1)

    txn0 = txn_usecase.make_replenishment(
        balance=balance, amount=1050, created_at=one_minute_ago
    )
    assert txn0.balance_remainder == 1050
    assert txn0.amount == 1050
    assert models.Balance.get().amount == 1050

    txn1 = txn_usecase.make_replenishment(
        balance=balance, amount=2025, created_at=after_one_minute
    )
    assert txn1.balance_remainder == 3075
    assert txn1.amount == 2025
    assert models.Balance.get().amount == 3075

    txn2 = txn_usecase.make_replenishment(balance=balance, amount=500, created_at=now)
    assert txn2.balance_remainder == 1550
    assert txn2.amount == 500
    assert models.Balance.get().amount == 3575

    assert models.Transaction.get(id=txn0.id).balance_remainder == 1050
    assert models.Transaction.get(id=txn0.id).amount == 1050

    assert models.Transaction.get(id=txn1.id).balance_remainder == 3575
    assert models.Transaction.get(id=txn1.id).amount == 2025


@pytest.mark.usefixtures("with_memory_database")
def test_sametime_created_txn_calculation_between_txns(
    make_account, make_currency, make_balance
):
    balance = make_balance(make_account(), make_currency())

    now = datetime.now()
    one_minute_ago = now - timedelta(minutes=1)
    after_one_minute = now + timedelta(minutes=1)

    txn0 = txn_usecase.make_replenishment(
        balance=balance, amount=1050, created_at=one_minute_ago
    )
    assert txn0.balance_remainder == 1050
    assert txn0.amount == 1050
    assert models.Balance.get().amount == 1050

    txn1 = txn_usecase.make_replenishment(balance=balance, amount=2025, created_at=now)
    assert txn1.balance_remainder == 3075
    assert txn1.amount == 2025
    assert models.Balance.get().amount == 3075

    txn2 = txn_usecase.make_replenishment(
        balance=balance, amount=500, created_at=after_one_minute
    )
    assert txn2.balance_remainder == 3575
    assert txn2.amount == 500
    assert models.Balance.get().amount == 3575

    txn3 = txn_usecase.make_replenishment(balance=balance, amount=200, created_at=now)
    assert txn3.balance_remainder == 3275
    assert txn3.amount == 200
    assert models.Balance.get().amount == 3775

    assert models.Transaction.get(id=txn0.id).balance_remainder == 1050
    assert models.Transaction.get(id=txn0.id).amount == 1050

    assert models.Transaction.get(id=txn1.id).balance_remainder == 3275
    assert models.Transaction.get(id=txn1.id).amount == 2025

    assert models.Transaction.get(id=txn2.id).balance_remainder == 3775
    assert models.Transaction.get(id=txn2.id).amount == 500
