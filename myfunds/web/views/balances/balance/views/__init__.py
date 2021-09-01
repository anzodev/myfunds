from functools import wraps

from flask import Blueprint
from flask import abort
from flask import g

from myfunds.core.models import Balance


bp = Blueprint(
    "balance",
    __name__,
    url_prefix="/balances/<int:balance_id>",
    template_folder="../templates",
)


def verify_balance(f):
    @wraps(f)
    def wrapper(balance_id: int, *args, **kwargs):
        balance = Balance.get_or_none(id=balance_id, account=g.authorized_account)
        if balance is None:
            abort(404)

        g.balance = balance
        g.currency = balance.currency

        return f(*args, **kwargs)

    return wrapper
