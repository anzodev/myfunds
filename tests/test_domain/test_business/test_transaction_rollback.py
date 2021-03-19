import datetime

import pytest

from myfunds.domain import business
from myfunds.domain import models


@pytest.mark.usefixtures("db_transaction_ctx")
def test_txn_param_verify(new_account, new_currency, new_balance, new_replenishment):
    balance = new_balance(new_account(), new_currency())
    unknown_txn = new_replenishment(balance=balance)
    unknown_txn.type_ = "unknown"

    with pytest.raises(ValueError):
        business.rollback_transaction(balance)
        business.rollback_transaction(unknown_txn)


@pytest.mark.usefixtures("db_transaction_ctx")
def test_replenishment_rollback_calc(new_account, new_currency, new_balance):
    balance = new_balance(new_account(), new_currency())
    txn = business.make_replenishment(balance=balance, amount=2025)

    business.rollback_transaction(txn)
    assert models.Transaction.select().count() == 0
    assert models.Balance.get().amount == 0


@pytest.mark.usefixtures("db_transaction_ctx")
def test_replenishment_rollback_calc_after_txn(new_account, new_currency, new_balance):
    utc_now = datetime.datetime.utcnow()
    utc_1m_after = utc_now + datetime.timedelta(minutes=1)

    balance = new_balance(new_account(), new_currency())
    business.make_replenishment(balance=balance, amount=2025, created_at=utc_now)
    txn = business.make_replenishment(
        balance=balance, amount=1050, created_at=utc_1m_after
    )

    business.rollback_transaction(txn)
    assert models.Transaction.select().count() == 1
    assert models.Balance.get().amount == 2025

    assert models.Transaction.get().balance_remainder == 2025
    assert models.Transaction.get().amount == 2025


@pytest.mark.usefixtures("db_transaction_ctx")
def test_replenishment_rollback_calc_before_txn(new_account, new_currency, new_balance):
    utc_now = datetime.datetime.utcnow()
    utc_1m_before = utc_now - datetime.timedelta(minutes=1)

    balance = new_balance(new_account(), new_currency())
    txn0 = business.make_replenishment(
        balance=balance, amount=1050, created_at=utc_1m_before
    )
    txn1 = business.make_replenishment(balance=balance, amount=2025, created_at=utc_now)
    assert txn1.balance_remainder == 3075

    business.rollback_transaction(txn0)
    assert models.Transaction.select().count() == 1
    assert models.Balance.get().amount == 2025

    assert models.Transaction.get().balance_remainder == 2025
    assert models.Transaction.get().amount == 2025


@pytest.mark.usefixtures("db_transaction_ctx")
def test_replenishment_rollback_calc_between_txns(
    new_account, new_currency, new_balance
):
    utc_now = datetime.datetime.utcnow()
    utc_1m_before = utc_now - datetime.timedelta(minutes=1)
    utc_1m_after = utc_now + datetime.timedelta(minutes=1)

    balance = new_balance(new_account(), new_currency())
    txn0 = business.make_replenishment(
        balance=balance, amount=1050, created_at=utc_1m_before
    )
    txn1 = business.make_replenishment(balance=balance, amount=2025, created_at=utc_now)
    txn2 = business.make_replenishment(
        balance=balance, amount=500, created_at=utc_1m_after
    )
    assert txn2.balance_remainder == 3575

    business.rollback_transaction(txn1)
    assert models.Transaction.select().count() == 2
    assert models.Balance.get().amount == 1550

    assert models.Transaction.get(id=txn0.id).balance_remainder == 1050
    assert models.Transaction.get(id=txn0.id).amount == 1050

    assert models.Transaction.get(id=txn2.id).balance_remainder == 1550
    assert models.Transaction.get(id=txn2.id).amount == 500


@pytest.mark.usefixtures("db_transaction_ctx")
def test_sametime_replenishment_rollback_calc(new_account, new_currency, new_balance):
    utc_now = datetime.datetime.utcnow()

    balance = new_balance(new_account(), new_currency())
    txn0 = business.make_replenishment(balance=balance, amount=1050, created_at=utc_now)
    txn1 = business.make_replenishment(balance=balance, amount=2025, created_at=utc_now)
    assert txn1.balance_remainder == 3075

    business.rollback_transaction(txn0)
    assert models.Transaction.select().count() == 1
    assert models.Balance.get().amount == 2025

    assert models.Transaction.get(id=txn1.id).balance_remainder == 2025
    assert models.Transaction.get(id=txn1.id).amount == 2025
