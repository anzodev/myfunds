from functools import wraps

from flask import Blueprint
from flask import abort
from flask import g

from myfunds.core.models import Balance
from myfunds.core.models import Category
from myfunds.web import utils
from myfunds.web.constants import FundsDirection


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

        # fmt: off
        expense_categories = (
            Category
            .select()
            .where(
                (Category.account == g.authorized_account)
                & (Category.direction == FundsDirection.EXPENSE.value)
            )
            .order_by(Category.name)
        )
        income_categories = (
            Category
            .select()
            .where(
                (Category.account == g.authorized_account)
                & (Category.direction == FundsDirection.INCOME.value)
            )
            .order_by(Category.name)
        )
        # fmt: on

        g.balance = balance
        g.currency = balance.currency
        g.amount_placeholder = utils.make_amount_placeholder(g.currency.precision)
        g.amount_pattern = utils.make_amount_pattern(g.currency.precision)
        g.expense_categories = expense_categories
        g.income_categories = income_categories

        return f(*args, **kwargs)

    return wrapper
