import datetime

import pytest

from myfunds.domain import business
from myfunds.domain import models


@pytest.mark.usefixtures("db_transaction_ctx")
def test_regular_creation(new_account, new_currency, execution_timing):
    account = new_account()
    currency = new_currency()

    t0, t1, _ = execution_timing(business.create_balance)(account, currency, "test")

    assert models.Balance.select().count() == 1
    balance = models.Balance.get()

    assert balance.account == account
    assert balance.currency == currency
    assert balance.name == "test"
    assert balance.amount == 0
    assert (
        datetime.datetime.utcfromtimestamp(t0)
        < balance.created_at
        < datetime.datetime.utcfromtimestamp(t1)
    )


@pytest.mark.usefixtures("db_transaction_ctx")
def test_account_param_verify(new_currency):
    currency = new_currency()

    with pytest.raises(ValueError):
        business.create_balance(currency, currency, "test")


@pytest.mark.usefixtures("db_transaction_ctx")
def test_currency_param_verify(new_account):
    account = new_account()

    with pytest.raises(ValueError):
        business.create_balance(account, account, "test")


@pytest.mark.usefixtures("db_transaction_ctx")
def test_name_param_verify(new_account, new_currency):
    account = new_account()
    currency = new_currency()

    with pytest.raises(ValueError):
        business.create_balance(account, currency, 100)
        business.create_balance(account, currency, "")
