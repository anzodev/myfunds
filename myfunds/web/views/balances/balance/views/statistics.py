from calendar import monthrange
from collections import namedtuple
from datetime import date
from datetime import datetime
from typing import List
from typing import Optional
from typing import Set
from typing import Tuple

import peewee as pw
from flask import current_app
from flask import g
from flask import render_template
from flask import request
from flask import url_for
from wtforms import Form
from wtforms import IntegerField
from wtforms import ValidationError
from wtforms import validators as vals
from wtforms.fields.core import StringField

from myfunds.core.models import BalanceLimit
from myfunds.core.models import Category
from myfunds.core.models import Transaction
from myfunds.web import auth
from myfunds.web import utils
from myfunds.web.constants import DATETIME_FORMAT
from myfunds.web.constants import NO_CATEGORY_ID
from myfunds.web.constants import NO_CATEGORY_TXN_COLOR
from myfunds.web.constants import FundsDirection
from myfunds.web.views.balances.balance.views import bp
from myfunds.web.views.balances.balance.views import verify_balance


def make_stats_years() -> List[int]:
    years = current_app.config["BALANCE_STATISTICS_YEARS"]
    current_year = utils.current_year()
    return [current_year] + [current_year - i for i in range(1, years + 1)]


def make_date_range_by_year_and_month(year: int, month: int) -> Tuple[date, date]:
    until_year = year if month < 12 else year + 1
    until_month = month + 1 if month < 12 else 1
    return (date(year, month, 1), date(until_year, until_month, 1))


def calculate_start_balance(stats_range: Tuple[datetime, datetime]) -> int:
    # fmt: off
    last_txn_of_previous_month = (
        Transaction
        .select()
        .where(
            (Transaction.balance == g.balance)
            & (Transaction.created_at < stats_range[0])
        )
        .order_by(Transaction.created_at.desc())
        .first()
    )
    # fmt: on

    result = None
    if last_txn_of_previous_month is not None:
        result = last_txn_of_previous_month.balance_remainder

    return result


def calculate_end_balance(stats_range: Tuple[datetime, datetime]) -> int:
    # fmt: off
    last_txn_of_current_month = (
        Transaction
        .select()
        .where(
            (Transaction.balance == g.balance)
            & (Transaction.created_at.between(*stats_range))
        )
        .order_by(Transaction.created_at.desc())
        .first()
    )
    # fmt: on

    result = None
    if last_txn_of_current_month is not None:
        result = last_txn_of_current_month.balance_remainder

    return result


def calculate_expense(
    stats_range: Tuple[datetime, datetime], excluded_categories: Set[int]
) -> int:
    excluded_categories = excluded_categories.copy()
    exclude_no_category = NO_CATEGORY_ID in excluded_categories
    excluded_categories.discard(NO_CATEGORY_ID)

    # fmt: off
    excluded_categories_condition = (
        (Transaction.category.not_in(excluded_categories))
        | (Transaction.category.is_null(True))
    )
    if exclude_no_category:
        excluded_categories_condition = (
            (Transaction.category.not_in(excluded_categories))
            & (Transaction.category.is_null(False))
        )
    # fmt: on

    # fmt: off
    return (
        Transaction
        .select(pw.fn.SUM(Transaction.amount))
        .where(
            (Transaction.balance == g.balance)
            & (Transaction.direction == FundsDirection.EXPENSE.value)
            & (Transaction.created_at.between(*stats_range))
            & excluded_categories_condition
        )
        .scalar()
    )
    # fmt: on


def calculate_income(stats_range: Tuple[datetime, datetime]) -> int:
    # fmt: off
    return (
        Transaction
        .select(pw.fn.SUM(Transaction.amount))
        .where(
            (Transaction.balance == g.balance)
            & (Transaction.direction == FundsDirection.INCOME.value)
            & (Transaction.created_at.between(*stats_range))
        )
        .scalar()
    )
    # fmt: on


def calculate_general_stats(
    stats_range: Tuple[datetime, datetime], excluded_categories: Set[int]
) -> dict:
    year, month = stats_range[0].year, stats_range[0].month

    start_balance = calculate_start_balance(stats_range)
    expense = calculate_expense(stats_range, excluded_categories)
    income = calculate_income(stats_range)

    end_balance = None
    if year != utils.current_year() or month != utils.current_month():
        end_balance = calculate_end_balance(stats_range)

    expense_pct, savings, savings_pct = None, None, None
    if start_balance is not None and expense is not None:
        expense_pct = round((expense / start_balance) * 100, 2)
        savings = start_balance - expense
        savings_pct = round((savings / start_balance) * 100, 2)

    return {
        "start_balance": start_balance,
        "expense": expense,
        "expense_pct": expense_pct,
        "income": income,
        "end_balance": end_balance,
        "savings": savings,
        "savings_pct": savings_pct,
    }


def calculate_expense_categories_stats(
    stats_range: Tuple[datetime, datetime], excluded_categories: Set[int]
) -> List[dict]:
    # fmt: off
    query = (
        Category
        .select(
            Category.id,
            Category.name,
            Category.color_sign,
            pw.fn.SUM(Transaction.amount).alias("amount"),
        )
        .join(Transaction)
        .where(
            (Category.account == g.authorized_account)
            & (Category.direction == FundsDirection.EXPENSE.value)
            & (Transaction.balance_id == g.balance.id)
            & (Transaction.created_at.between(*stats_range))
        )
        .group_by(Category.id)
    )
    # fmt: on

    # fmt: off
    no_category_txns_amount = (
        Transaction
        .select(pw.fn.SUM(Transaction.amount))
        .where(
            (Transaction.balance == g.balance)
            & (Transaction.direction == FundsDirection.EXPENSE.value)
            & (Transaction.category.is_null())
            & (Transaction.created_at.between(*stats_range))
        )
        .scalar()
    )
    # fmt: on

    # fmt: off
    balance_limits = (
        BalanceLimit
        .select()
        .where(
            (BalanceLimit.balance == g.balance)
        )
    )
    # fmt: on

    expense = calculate_expense(stats_range, excluded_categories)

    exclude_no_category = NO_CATEGORY_ID in excluded_categories

    categories_limit_amounts = {i.category_id: i.amount for i in balance_limits}

    top_expense = max(
        [i.amount for i in query if i.id not in excluded_categories]
        + [(no_category_txns_amount if not exclude_no_category else 0) or 0]
    )

    result = []
    for i in query:
        result.append(
            {
                "name": i.name,
                "color_sign": i.color_sign,
                "transactions_link": make_transactions_link(i.id, stats_range),
                "amount": i.amount,
                "amount_pct": (
                    round((i.amount / expense) * 100, 2) if expense else None
                ),
                "amount_ratio": (
                    round((i.amount / top_expense) * 100, 2) if top_expense else None
                ),
                "expense_limit": init_expense_limit_params(
                    i.amount, categories_limit_amounts.get(i.id)
                ),
                "is_excluded": i.id in excluded_categories,
                "exclusion_link": make_exclusion_link(excluded_categories, i.id),
            }
        )

    if no_category_txns_amount is not None and no_category_txns_amount > 0:
        result.append(
            {
                "name": "No category",
                "color_sign": NO_CATEGORY_TXN_COLOR,
                "transactions_link": make_transactions_link(
                    NO_CATEGORY_ID, stats_range
                ),
                "amount": no_category_txns_amount,
                "amount_pct": (
                    round((no_category_txns_amount / expense) * 100, 2)
                    if expense
                    else None
                ),
                "amount_ratio": (
                    round((no_category_txns_amount / top_expense) * 100, 2)
                    if top_expense
                    else None
                ),
                "expense_limit": init_expense_limit_params(
                    no_category_txns_amount, None
                ),
                "is_excluded": exclude_no_category,
                "exclusion_link": make_exclusion_link(
                    excluded_categories, NO_CATEGORY_ID
                ),
            }
        )

    result = sorted(
        result, key=lambda i: 0 if i["is_excluded"] else i["amount"], reverse=True
    )
    return result


def make_transactions_link(
    category_id: int, stats_range: Tuple[datetime, datetime]
) -> str:
    return url_for(
        "balances.i.transactions",
        balance_id=g.balance.id,
        direction=FundsDirection.EXPENSE.value,
        category_id=category_id,
        created_at_range_hrf=" - ".join(i.strftime(DATETIME_FORMAT) for i in stats_range),
    )


def make_exclusion_link(excluded_categories: Set[int], category_id: int) -> str:
    excluded_categories = excluded_categories.copy()
    if category_id in excluded_categories:
        excluded_categories.discard(category_id)
    else:
        excluded_categories.add(category_id)

    args = request.args.copy()
    args["excluded_categories"] = ",".join(str(i) for i in excluded_categories)

    return url_for("balances.i.statistics", balance_id=g.balance.id, **args)


ExpenseLimitParams = namedtuple(
    "ExpenseLimitParams", ["amount", "percent", "css_text_color"]
)


def init_expense_limit_params(
    category_amount: int, limit_amount: Optional[int] = None
) -> ExpenseLimitParams:
    if limit_amount is None:
        return ExpenseLimitParams(None, None, None)

    percent = round((category_amount / limit_amount) * 100, 2)
    if percent > 100:
        percent = round((100 - percent), 2)

    if 0 <= percent < 60:
        css_text_color = "text-success"
    elif 60 <= percent < 80:
        css_text_color = "text-warning"
    elif 80 <= percent or percent < 0:
        css_text_color = "text-danger"
    else:
        css_text_color = None

    return ExpenseLimitParams(limit_amount, percent, css_text_color)


class StatisticsFilterForm(Form):
    year = IntegerField(validators=[vals.Optional()])
    month = IntegerField(validators=[vals.Optional(), vals.AnyOf(list(range(1, 13)))])
    excluded_categories = StringField(
        validators=[vals.Optional(), vals.Regexp(r"^-?\d+(,-?\d+?)*$")]
    )

    def validate_year(form, field) -> None:
        year = field.data
        if year not in make_stats_years():
            raise ValidationError(f"Can't show statistics for the {year} year.")


@bp.route("/statistics")
@auth.login_required
@verify_balance
def statistics():
    filter_form = StatisticsFilterForm(request.args)
    utils.validate_form(
        filter_form,
        url_for("balances.i.statistics", balance_id=g.balance.id),
        error_notify=None,
    )

    current_year, current_month = utils.current_year(), utils.current_month()

    year = filter_form.year.data or current_year
    month = filter_form.month.data or current_month
    excluded_categories = set(
        int(i) for i in filter_form.excluded_categories.data.split(",") if i != ""
    )

    # Set the December month if month parameter not set and year parameter isn't
    # equal to the current year.
    if year < current_year and filter_form.month.data is None:
        month = 12

    disabled_months = (
        list(range(1, 13))[-(12 - current_month) :] if year == current_year else []
    )

    # Set last allowed month if the month number is in disabled months list.
    if month in disabled_months:
        month = disabled_months[0] - 1

    filters = {
        "allowed_years": make_stats_years(),
        "year": year,
        "disabled_months": disabled_months,
        "month": month,
    }

    current_day = None
    if year == current_year and month == current_month:
        today = date.today()
        month_completed_by = round((today.day / monthrange(year, month)[1]) * 100, 2)
        current_day = f"{today.day} ({today.strftime('%A')}, {month_completed_by}%)"

    stats_range = make_date_range_by_year_and_month(year, month)
    general_stats = calculate_general_stats(stats_range, excluded_categories)
    expense_categories_stats = calculate_expense_categories_stats(
        stats_range, excluded_categories
    )

    return render_template(
        "balance/statistics.html",
        filters=filters,
        current_day=current_day,
        general_stats=general_stats,
        expense_categories_stats=expense_categories_stats,
    )
