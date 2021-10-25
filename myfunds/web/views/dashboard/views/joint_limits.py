from datetime import date
from datetime import datetime
from typing import List
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

from myfunds.core.models import Balance
from myfunds.core.models import Category
from myfunds.core.models import JointLimit
from myfunds.core.models import JointLimitParticipant
from myfunds.core.models import Transaction
from myfunds.web import auth
from myfunds.web import utils
from myfunds.web.constants import FundsDirection
from myfunds.web.views.dashboard.views import bp


def make_stats_years() -> List[int]:
    years = current_app.config["DASHBOARD_JOINT_LIMITS_YEARS"]
    current_year = utils.current_year()
    return [current_year] + [current_year - i for i in range(1, years + 1)]


def make_date_range_by_year_and_month(year: int, month: int) -> Tuple[date, date]:
    until_year = year if month < 12 else year + 1
    until_month = month + 1 if month < 12 else 1
    return (date(year, month, 1), date(until_year, until_month, 1))


def build_joint_limits_info(stats_range: Tuple[datetime, datetime]) -> List[dict]:
    categories_ids_query = Category.select(Category.id).where(
        (Category.account == g.authorized_account)
        & (Category.direction == FundsDirection.EXPENSE.value)
    )
    categories_ids = [i.id for i in categories_ids_query]

    limits = (
        JointLimit.select()
        .join(JointLimitParticipant)
        .where(JointLimitParticipant.category_id.in_(categories_ids))
        .group_by(JointLimit.id)
    )

    result = []

    for limit in limits:
        data = {}
        data["limit"] = limit

        currency = limit.currency
        data["currency"] = currency

        participants = JointLimitParticipant.select().where(
            JointLimitParticipant.limit == limit
        )

        data["participants"] = []

        for p in participants:
            participant_data = {}

            category = p.category
            account = category.account

            participant_data["account"] = account
            participant_data["category"] = category

            # fmt: off
            expense_by_balances = (
                Balance
                .select(
                    Balance,
                    pw.fn.SUM(Transaction.amount).alias("expense_amount"),
                )
                .join(Transaction, pw.JOIN.LEFT_OUTER)
                .where(
                    (Balance.account == account)
                    & (Balance.currency == currency)
                    & (Transaction.category == category)
                    & (Transaction.created_at.between(*stats_range))
                )
                .group_by(Balance.id)
            )
            # fmt: on

            if not expense_by_balances:
                continue

            participant_data["balances"] = list(expense_by_balances)
            participant_data["balances_count"] = len(participant_data["balances"])
            participant_data["total_expense"] = sum(
                [i.expense_amount for i in participant_data["balances"]] + [0]
            )

            data["participants"].append(participant_data)

        if not data["participants"]:
            continue

        data["total_expense"] = sum([i["total_expense"] for i in data["participants"]])

        total_expense_pct = round((data["total_expense"] / limit.amount) * 100, 2)
        if total_expense_pct > 100:
            total_expense_pct = round(100 - total_expense_pct, 2)

        if 0 <= total_expense_pct < 60:
            css_text_color = "text-success"
        elif 60 <= total_expense_pct < 80:
            css_text_color = "text-warning"
        elif 80 <= total_expense_pct or total_expense_pct < 0:
            css_text_color = "text-danger"
        else:
            css_text_color = ""

        data["total_expense_pct"] = total_expense_pct
        data["total_expense_pct_color"] = css_text_color

        result.append(data)

    return result


class JointLimitsFilterForm(Form):
    year = IntegerField(validators=[vals.Optional()])
    month = IntegerField(validators=[vals.Optional(), vals.AnyOf(list(range(1, 13)))])

    def validate_year(form, field) -> None:
        year = field.data
        if year not in make_stats_years():
            raise ValidationError(f"Can't show joint limits info for the {year} year.")


@bp.route("/joint-limits")
@auth.login_required
def joint_limits():
    filter_form = JointLimitsFilterForm(request.args)
    utils.validate_form(
        filter_form, url_for("dashboard.joint_limits"), error_notify=None
    )

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

    stats_range = make_date_range_by_year_and_month(year, month)
    joint_limits_info = build_joint_limits_info(stats_range)

    return render_template(
        "joint-limits.html",
        filters=filters,
        joint_limits_info=joint_limits_info,
    )
