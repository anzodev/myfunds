import datetime

import pytest

from myfunds.domain import business
from myfunds.domain import constants
from myfunds.domain import models


@pytest.mark.usefixtures("db_transaction_ctx")
def test_call_with_default_params(
    new_account, new_currency, new_balance, execution_timing
):
    balance = new_balance(new_account(), new_currency())

    t0, t1, _ = execution_timing(business.make_withdrawal)(balance=balance, amount=100)

    assert models.Transaction.select().count() == 1
    txn = models.Transaction.get()
    assert txn.balance == balance
    assert txn.balance_remainder == -100
    assert txn.type_ == constants.TransactionType.WITHDRAWAL
    assert txn.group is None
    assert txn.amount == 100
    assert txn.comment is None
    assert (
        datetime.datetime.utcfromtimestamp(t0)
        < txn.created_at
        < datetime.datetime.utcfromtimestamp(t1)
    )


@pytest.mark.usefixtures("db_transaction_ctx")
def test_call_with_full_params(
    new_account, new_currency, new_balance, new_withdrawal_group
):
    account = new_account()
    balance = new_balance(account, new_currency())
    txn_group = new_withdrawal_group(account=account)
    created_at = datetime.datetime.utcnow()

    business.make_withdrawal(
        balance=balance,
        amount=100,
        txn_group=txn_group,
        comment="test withdrawal",
        created_at=created_at,
    )

    assert models.Transaction.select().count() == 1
    txn = models.Transaction.get()
    assert txn.balance == balance
    assert txn.balance_remainder == -100
    assert txn.type_ == constants.TransactionType.WITHDRAWAL
    assert txn.group == txn_group
    assert txn.amount == 100
    assert txn.comment == "test withdrawal"
    assert txn.created_at == created_at


@pytest.mark.usefixtures("db_transaction_ctx")
def test_balance_param_verify(new_account):
    account = new_account()

    with pytest.raises(ValueError):
        business.make_withdrawal(balance=account, amount=100)


@pytest.mark.usefixtures("db_transaction_ctx")
def test_amount_param_verify(new_account, new_currency, new_balance):
    balance = new_balance(new_account(), new_currency())

    with pytest.raises(ValueError):
        business.make_withdrawal(balance=balance, amount=0)
        business.make_withdrawal(balance=balance, amount=-1)
        business.make_withdrawal(balance=balance, amount=0.5)


@pytest.mark.usefixtures("db_transaction_ctx")
def test_txn_group_param_verify(
    new_account,
    new_currency,
    new_balance,
    new_replenishment_group,
    new_withdrawal_group,
):
    currency = new_currency()
    account1 = new_account("test_account1")
    account2 = new_account("test_account2")
    balance1 = new_balance(account1, currency)
    balance2 = new_balance(account2, currency)
    txn_withdrawal_group1 = new_withdrawal_group(account=account1)
    txn_withdrawal_group2 = new_withdrawal_group(account=account2)

    with pytest.raises(ValueError):
        business.make_withdrawal(balance=balance1, amount=1, txn_group=balance1)
        business.make_withdrawal(
            balance=balance1,
            amount=1,
            txn_group=new_replenishment_group(account=account1),
        )
        business.make_withdrawal(
            balance=balance1,
            amount=1,
            txn_group=txn_withdrawal_group2,
        )
        business.make_withdrawal(
            balance=balance2,
            amount=1,
            txn_group=txn_withdrawal_group1,
        )


@pytest.mark.usefixtures("db_transaction_ctx")
def test_comment_param_verify(new_account, new_currency, new_balance):
    balance = new_balance(new_account(), new_currency())

    with pytest.raises(ValueError):
        business.make_withdrawal(balance=balance, amount=1, comment=0)


@pytest.mark.usefixtures("db_transaction_ctx")
def test_created_at_param_verify(new_account, new_currency, new_balance):
    balance = new_balance(new_account(), new_currency())

    with pytest.raises(ValueError):
        business.make_withdrawal(balance=balance, amount=1, created_at=0)


@pytest.mark.usefixtures("db_transaction_ctx")
def test_first_txn_calc(new_account, new_currency, new_balance):
    balance = new_balance(new_account(), new_currency())

    txn = business.make_withdrawal(balance=balance, amount=2050)
    assert txn.balance_remainder == -2050
    assert txn.amount == 2050
    assert models.Balance.get().amount == -2050


@pytest.mark.usefixtures("db_transaction_ctx")
def test_second_txn_calc(new_account, new_currency, new_balance):
    balance = new_balance(new_account(), new_currency())

    txn0 = business.make_withdrawal(balance=balance, amount=1050)
    assert txn0.balance_remainder == -1050
    assert txn0.amount == 1050
    assert models.Balance.get().amount == -1050

    txn1 = business.make_withdrawal(balance=balance, amount=2025)
    assert txn1.balance_remainder == -3075
    assert txn1.amount == 2025
    assert models.Balance.get().amount == -3075


@pytest.mark.usefixtures("db_transaction_ctx")
def test_sametime_txn_calc(new_account, new_currency, new_balance):
    balance = new_balance(new_account(), new_currency())

    utc_now = datetime.datetime.utcnow()
    utc_1m_ago = utc_now - datetime.timedelta(minutes=1)

    txn0 = business.make_withdrawal(balance=balance, amount=1050, created_at=utc_1m_ago)
    assert txn0.balance_remainder == -1050
    assert txn0.amount == 1050
    assert models.Balance.get().amount == -1050

    txn1 = business.make_withdrawal(balance=balance, amount=2025, created_at=utc_now)
    assert txn1.balance_remainder == -3075
    assert txn1.amount == 2025
    assert models.Balance.get().amount == -3075

    txn2 = business.make_withdrawal(balance=balance, amount=500, created_at=utc_now)
    assert txn2.balance_remainder == -3575
    assert txn2.amount == 500
    assert models.Balance.get().amount == -3575

    assert models.Transaction.get(id=txn0.id).balance_remainder == -1050
    assert models.Transaction.get(id=txn0.id).amount == 1050

    assert models.Transaction.get(id=txn1.id).balance_remainder == -3575
    assert models.Transaction.get(id=txn1.id).amount == 2025


@pytest.mark.usefixtures("db_transaction_ctx")
def test_txn_calc_between_txns(new_account, new_currency, new_balance):
    balance = new_balance(new_account(), new_currency())

    utc_now = datetime.datetime.utcnow()
    utc_1m_ago = utc_now - datetime.timedelta(minutes=1)
    utc_1m_after = utc_now + datetime.timedelta(minutes=1)

    txn0 = business.make_withdrawal(balance=balance, amount=1050, created_at=utc_1m_ago)
    assert txn0.balance_remainder == -1050
    assert txn0.amount == 1050
    assert models.Balance.get().amount == -1050

    txn1 = business.make_withdrawal(
        balance=balance, amount=2025, created_at=utc_1m_after
    )
    assert txn1.balance_remainder == -3075
    assert txn1.amount == 2025
    assert models.Balance.get().amount == -3075

    txn2 = business.make_withdrawal(balance=balance, amount=500, created_at=utc_now)
    assert txn2.balance_remainder == -1550
    assert txn2.amount == 500
    assert models.Balance.get().amount == -3575

    assert models.Transaction.get(id=txn0.id).balance_remainder == -1050
    assert models.Transaction.get(id=txn0.id).amount == 1050

    assert models.Transaction.get(id=txn1.id).balance_remainder == -3575
    assert models.Transaction.get(id=txn1.id).amount == 2025


@pytest.mark.usefixtures("db_transaction_ctx")
def test_sametime_txn_calc_between_txns(new_account, new_currency, new_balance):
    balance = new_balance(new_account(), new_currency())

    utc_now = datetime.datetime.utcnow()
    utc_1m_ago = utc_now - datetime.timedelta(minutes=1)
    utc_1m_after = utc_now + datetime.timedelta(minutes=1)

    txn0 = business.make_withdrawal(balance=balance, amount=1050, created_at=utc_1m_ago)
    assert txn0.balance_remainder == -1050
    assert txn0.amount == 1050
    assert models.Balance.get().amount == -1050

    txn1 = business.make_withdrawal(balance=balance, amount=2025, created_at=utc_now)
    assert txn1.balance_remainder == -3075
    assert txn1.amount == 2025
    assert models.Balance.get().amount == -3075

    txn2 = business.make_withdrawal(
        balance=balance, amount=500, created_at=utc_1m_after
    )
    assert txn2.balance_remainder == -3575
    assert txn2.amount == 500
    assert models.Balance.get().amount == -3575

    txn3 = business.make_withdrawal(balance=balance, amount=200, created_at=utc_now)
    assert txn3.balance_remainder == -3275
    assert txn3.amount == 200
    assert models.Balance.get().amount == -3775

    assert models.Transaction.get(id=txn0.id).balance_remainder == -1050
    assert models.Transaction.get(id=txn0.id).amount == 1050

    assert models.Transaction.get(id=txn1.id).balance_remainder == -3275
    assert models.Transaction.get(id=txn1.id).amount == 2025

    assert models.Transaction.get(id=txn2.id).balance_remainder == -3775
    assert models.Transaction.get(id=txn2.id).amount == 500
