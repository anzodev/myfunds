from datetime import datetime
from datetime import timedelta

import pytest

from myfunds.core import models
from myfunds.core.usecase import transactions as txn_usecase
from myfunds.modules import check


@pytest.mark.usefixtures("with_memory_database")
def test_txn_value_checking(make_balance, make_replenishment):
    balance = make_balance()

    unknown_txn = make_replenishment(balance=balance)
    unknown_txn.direction = "unknown"

    with pytest.raises(check.ValidationError):
        txn_usecase.remove_transaction(balance)
        txn_usecase.remove_transaction(unknown_txn)


@pytest.mark.usefixtures("with_memory_database")
def test_replenishment_remove_calculation(make_balance):
    balance = make_balance()

    txn = txn_usecase.make_replenishment(balance=balance, amount=2025)

    txn_usecase.remove_transaction(txn)
    assert models.Transaction.select().count() == 0
    assert models.Balance.get().amount == 0


@pytest.mark.usefixtures("with_memory_database")
def test_replenishment_remove_calculation_after_txn(make_balance):
    now = datetime.now()
    after_one_minute = now + timedelta(minutes=1)

    balance = make_balance()
    txn_usecase.make_replenishment(balance=balance, amount=2025, created_at=now)
    txn = txn_usecase.make_replenishment(
        balance=balance, amount=1050, created_at=after_one_minute
    )

    txn_usecase.remove_transaction(txn)
    assert models.Transaction.select().count() == 1
    assert models.Balance.get().amount == 2025

    assert models.Transaction.get().balance_remainder == 2025
    assert models.Transaction.get().amount == 2025


@pytest.mark.usefixtures("with_memory_database")
def test_replenishment_remove_calculation_before_txn(make_balance):
    now = datetime.now()
    one_minute_ago = now - timedelta(minutes=1)

    balance = make_balance()
    txn0 = txn_usecase.make_replenishment(
        balance=balance, amount=1050, created_at=one_minute_ago
    )
    txn1 = txn_usecase.make_replenishment(balance=balance, amount=2025, created_at=now)
    assert txn1.balance_remainder == 3075

    txn_usecase.remove_transaction(txn0)
    assert models.Transaction.select().count() == 1
    assert models.Balance.get().amount == 2025

    assert models.Transaction.get().balance_remainder == 2025
    assert models.Transaction.get().amount == 2025


@pytest.mark.usefixtures("with_memory_database")
def test_replenishment_remove_calculation_between_txns(make_balance):
    now = datetime.now()
    one_minute_ago = now - timedelta(minutes=1)
    after_one_minute = now + timedelta(minutes=1)

    balance = make_balance()
    txn0 = txn_usecase.make_replenishment(
        balance=balance, amount=1050, created_at=one_minute_ago
    )
    txn1 = txn_usecase.make_replenishment(balance=balance, amount=2025, created_at=now)
    txn2 = txn_usecase.make_replenishment(
        balance=balance, amount=500, created_at=after_one_minute
    )
    assert txn2.balance_remainder == 3575

    txn_usecase.remove_transaction(txn1)
    assert models.Transaction.select().count() == 2
    assert models.Balance.get().amount == 1550

    assert models.Transaction.get(id=txn0.id).balance_remainder == 1050
    assert models.Transaction.get(id=txn0.id).amount == 1050

    assert models.Transaction.get(id=txn2.id).balance_remainder == 1550
    assert models.Transaction.get(id=txn2.id).amount == 500


@pytest.mark.usefixtures("with_memory_database")
def test_sametime_created_replenishment_remove_calculation(make_balance):
    now = datetime.now()

    balance = make_balance()
    txn0 = txn_usecase.make_replenishment(balance=balance, amount=1050, created_at=now)
    txn1 = txn_usecase.make_replenishment(balance=balance, amount=2025, created_at=now)
    assert txn1.balance_remainder == 3075

    txn_usecase.remove_transaction(txn0)
    assert models.Transaction.select().count() == 1
    assert models.Balance.get().amount == 2025

    assert models.Transaction.get(id=txn1.id).balance_remainder == 2025
    assert models.Transaction.get(id=txn1.id).amount == 2025


@pytest.mark.usefixtures("with_memory_database")
def test_withdrawal_remove_calculation(make_balance):
    balance = make_balance()

    txn = txn_usecase.make_withdrawal(balance=balance, amount=2025)

    txn_usecase.remove_transaction(txn)
    assert models.Transaction.select().count() == 0
    assert models.Balance.get().amount == 0


@pytest.mark.usefixtures("with_memory_database")
def test_withdrawal_remove_calculation_after_txn(make_balance):
    now = datetime.now()
    after_one_minute = now + timedelta(minutes=1)

    balance = make_balance()
    txn_usecase.make_withdrawal(balance=balance, amount=2025, created_at=now)
    txn = txn_usecase.make_withdrawal(
        balance=balance, amount=1050, created_at=after_one_minute
    )

    txn_usecase.remove_transaction(txn)
    assert models.Transaction.select().count() == 1
    assert models.Balance.get().amount == -2025

    assert models.Transaction.get().balance_remainder == -2025
    assert models.Transaction.get().amount == 2025


@pytest.mark.usefixtures("with_memory_database")
def test_withdrawal_remove_calculation_before_txn(make_balance):
    now = datetime.now()
    one_minute_ago = now - timedelta(minutes=1)

    balance = make_balance()
    txn0 = txn_usecase.make_withdrawal(
        balance=balance, amount=1050, created_at=one_minute_ago
    )
    txn1 = txn_usecase.make_withdrawal(balance=balance, amount=2025, created_at=now)
    assert txn1.balance_remainder == -3075

    txn_usecase.remove_transaction(txn0)
    assert models.Transaction.select().count() == 1
    assert models.Balance.get().amount == -2025

    assert models.Transaction.get().balance_remainder == -2025
    assert models.Transaction.get().amount == 2025


@pytest.mark.usefixtures("with_memory_database")
def test_withdrawal_remove_calculation_between_txns(make_balance):
    now = datetime.now()
    one_minute_ago = now - timedelta(minutes=1)
    after_one_minute = now + timedelta(minutes=1)

    balance = make_balance()
    txn0 = txn_usecase.make_withdrawal(
        balance=balance, amount=1050, created_at=one_minute_ago
    )
    txn1 = txn_usecase.make_withdrawal(balance=balance, amount=2025, created_at=now)
    txn2 = txn_usecase.make_withdrawal(
        balance=balance, amount=500, created_at=after_one_minute
    )
    assert txn2.balance_remainder == -3575

    txn_usecase.remove_transaction(txn1)
    assert models.Transaction.select().count() == 2
    assert models.Balance.get().amount == -1550

    assert models.Transaction.get(id=txn0.id).balance_remainder == -1050
    assert models.Transaction.get(id=txn0.id).amount == 1050

    assert models.Transaction.get(id=txn2.id).balance_remainder == -1550
    assert models.Transaction.get(id=txn2.id).amount == 500


@pytest.mark.usefixtures("with_memory_database")
def test_sametime_created_withdrawal_remove_calculation(make_balance):
    now = datetime.now()

    balance = make_balance()
    txn0 = txn_usecase.make_withdrawal(balance=balance, amount=1050, created_at=now)
    txn1 = txn_usecase.make_withdrawal(balance=balance, amount=2025, created_at=now)
    assert txn1.balance_remainder == -3075

    txn_usecase.remove_transaction(txn0)
    assert models.Transaction.select().count() == 1
    assert models.Balance.get().amount == -2025

    assert models.Transaction.get(id=txn1.id).balance_remainder == -2025
    assert models.Transaction.get(id=txn1.id).amount == 2025
