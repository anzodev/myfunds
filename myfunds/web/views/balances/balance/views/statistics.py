from calendar import monthrange
from collections import namedtuple
from datetime import date
from datetime import datetime
from typing import Optional

import peewee as pw
from flask import current_app
from flask import g
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
from wtforms import Form
from wtforms import IntegerField
from wtforms import ValidationError
from wtforms import validators as vals

from myfunds.core.models import Category
from myfunds.core.models import CategoryMonthLimit
from myfunds.core.models import Transaction
from myfunds.web import auth
from myfunds.web import utils
from myfunds.web.constants import DATETIME_FORMAT, NO_CATEGORY_TXN_COLOR
from myfunds.web.constants import FundsDirection
from myfunds.web.views.balances.balance.views import bp
from myfunds.web.views.balances.balance.views import verify_balance


class StatisticsFilterForm(Form):
    year = IntegerField(validators=[vals.Optional()])
    month = IntegerField(validators=[vals.Optional(), vals.AnyOf(list(range(1, 13)))])

    def validate_year(form, field) -> None:
        year = field.data
        if year not in make_stats_years():
            raise ValidationError(f"Can't show statistics for the {year} year.")


def make_stats_years() -> list[int]:
    years = current_app.config["BALANCE_STATISTICS_YEARS"]
    current_year = utils.current_year()
    return [current_year] + [current_year - i for i in range(1, years + 1)]


def make_date_range_by_year_and_month(year: int, month: int) -> tuple[date, date]:
    until_year = year if month < 12 else year + 1
    until_month = month + 1 if month < 12 else 1
    return (date(year, month, 1), date(until_year, until_month, 1))


def calculate_start_balance(stats_range: tuple[datetime, datetime]) -> int:
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


def calculate_end_balance(stats_range: tuple[datetime, datetime]) -> int:
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


def calculate_expense(stats_range: tuple[datetime, datetime]) -> int:
    # fmt: off
    return (
        Transaction
        .select(pw.fn.SUM(Transaction.amount))
        .where(
            (Transaction.balance == g.balance)
            & (Transaction.direction == FundsDirection.EXPENSE.value)
            & (Transaction.created_at.between(*stats_range))
        )
        .scalar()
    )
    # fmt: on


def calculate_income(stats_range: tuple[datetime, datetime]) -> int:
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


def calculate_general_stats(stats_range: tuple[datetime, datetime]) -> dict:
    year, month = stats_range[0].year, stats_range[0].month

    start_balance = calculate_start_balance(stats_range)
    expense = calculate_expense(stats_range)
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
    stats_range: tuple[datetime, datetime]
) -> list[dict]:
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
    month_limits = (
        CategoryMonthLimit
        .select()
        .where(
            (CategoryMonthLimit.balance == g.balance)
        )
    )
    # fmt: on

    categories_month_limit = {i.category_id: i.limit for i in month_limits}

    top_expense = max([i.amount for i in query] + [no_category_txns_amount or 0])

    expense = calculate_expense(stats_range)

    result = []
    for i in query:
        result.append(
            {
                "name": i.name,
                "color_sign": i.color_sign,
                "href": url_for(
                    "balances.i.transactions",
                    balance_id=g.balance.id,
                    direction=FundsDirection.EXPENSE.value,
                    category_id=i.id,
                    created_at_between=" - ".join(
                        i.strftime(DATETIME_FORMAT.value) for i in stats_range
                    ),
                ),
                "amount": i.amount,
                "amount_pct": round((i.amount / expense) * 100, 2),
                "amount_ratio": round((i.amount / top_expense) * 100, 2),
                "month_limit": init_month_limit(
                    i.amount, categories_month_limit.get(i.id)
                ),
            }
        )

    if no_category_txns_amount is not None and no_category_txns_amount > 0:
        result.append(
            {
                "name": "No category",
                "color_sign": NO_CATEGORY_TXN_COLOR,
                "href": url_for(
                    "balances.i.transactions",
                    balance_id=g.balance.id,
                    direction=FundsDirection.EXPENSE.value,
                    category_id=-1,
                    created_at_between=" - ".join(
                        i.strftime(DATETIME_FORMAT.value) for i in stats_range
                    ),
                ),
                "amount": no_category_txns_amount,
                "amount_pct": round((no_category_txns_amount / expense) * 100, 2),
                "amount_ratio": round((no_category_txns_amount / top_expense) * 100, 2),
                "month_limit": init_month_limit(i.amount, None),
            }
        )

    result = sorted(result, key=lambda i: i["amount"], reverse=True)
    return result


MonthLimit = namedtuple("MonthLimit", ["value", "percent", "css_text_color"])


def init_month_limit(
    category_amount: int, limit_value: Optional[int] = None
) -> MonthLimit:
    if limit_value is None:
        return MonthLimit(None, None, None)

    percent = round((category_amount / limit_value) * 100, 2)
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

    return MonthLimit(limit_value, percent, css_text_color)


@bp.route("/statistics")
@auth.login_required
@verify_balance
def statistics():
    filter_form = StatisticsFilterForm(request.args)
    if not filter_form.validate():
        return redirect(url_for("balances.i.statistics", balance_id=g.balance.id))

    current_year, current_month = utils.current_year(), utils.current_month()

    year = filter_form.year.data or current_year
    month = filter_form.month.data or current_month

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
    general_stats = calculate_general_stats(stats_range)
    expense_categories_stats = calculate_expense_categories_stats(stats_range)

    return render_template(
        "balance/statistics.html",
        filters=filters,
        current_day=current_day,
        general_stats=general_stats,
        expense_categories_stats=expense_categories_stats,
    )
