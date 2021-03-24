import calendar
import datetime
import itertools
import logging
from functools import wraps

import peewee as pw
from flask import abort
from flask import current_app as app
from flask import g
from flask import render_template
from flask import request
from playhouse.flask_utils import PaginatedQuery

from myfunds.domain import models
from myfunds.domain.constants import TransactionType
from myfunds.tools import dates
from myfunds.web import constants
from myfunds.web.tools import auth
from myfunds.web.tools import translates


_logger = logging.getLogger(__name__)


def _page_init(f):
    @wraps(f)
    def wrapper(balance_id: int, *args, **kwargs):
        g.txn_types_const = TransactionType
        g.txn_types = translates.TXN_TYPES
        g.balance = (
            models.Balance.select(
                models.Balance,
                models.Currency,
            )
            .join(models.Currency)
            .where(
                (models.Balance.id == balance_id)
                & (models.Balance.account == g.account)
            )
            .first()
        )
        if g.balance is None:
            abort(404)

        replenishments = models.Transaction.select(models.Transaction.id).where(
            (models.Transaction.type_ == TransactionType.REPLENISHMENT)
            & (models.Transaction.balance == g.balance)
        )
        withdrawals = models.Transaction.select(models.Transaction.id).where(
            (models.Transaction.type_ == TransactionType.WITHDRAWAL)
            & (models.Transaction.balance == g.balance)
        )

        g.balance_stats = {
            "replenishments_qty": replenishments.count(),
            "withdrawals_qty": withdrawals.count(),
        }

        return f(*args, **kwargs)

    return wrapper


@auth.login_required
@_page_init
def edit():
    return render_template("pages/balance/edit.html")


@auth.login_required
@_page_init
def transactions():
    tz = app.config["TIMEZONE"]
    dt_format = constants.DATETIME_FORMAT

    param_page = int(request.args.get("page", 1))
    param_limit = int(request.args.get("limit", 15))
    param_txn_type = request.args.get("txn_type")
    param_txn_group = request.args.get("txn_group")
    param_created_at_range = request.args.get("created_at_range")

    if param_created_at_range is None:
        since_dt, until_dt = dates.make_local_range_since_first_month_day_to_now(tz)
        param_created_at_range = " - ".join(
            [since_dt.strftime(dt_format), until_dt.strftime(dt_format)]
        )

    try:
        since_dt_str, until_dt_str = param_created_at_range.split(" - ")
        since_dt = dates.make_utc_from_dt_str(since_dt_str, dt_format, tz)
        until_dt = dates.make_utc_from_dt_str(until_dt_str, dt_format, tz)
    except Exception:
        _logger.exception("unexpected error while 'created_at_range' paramter parsing")
        param_created_at_range = None

    # _logger.debug(f"since_dt={since_dt}, until_dt={until_dt}")

    query = (
        models.Transaction.select(
            models.Transaction.id,
            models.Transaction.type_,
            models.Transaction.amount,
            models.Transaction.balance_remainder,
            models.Transaction.comment,
            models.Transaction.created_at,
            models.Balance,
            models.TransactionGroup,
        )
        .join(models.Balance)
        .switch()
        .join(models.TransactionGroup, pw.JOIN.LEFT_OUTER)
        .where(
            (models.Transaction.balance == g.balance)
            & (models.Transaction.created_at.between(since_dt, until_dt))
        )
        .order_by(models.Transaction.created_at.desc())
    )

    if param_txn_type in TransactionType:
        query = query.where(models.Transaction.type_ == param_txn_type)

    if param_txn_group is not None and param_txn_group == "NO_GROUP":
        query = query.where(models.Transaction.group.is_null())
    else:
        txn_group = models.TransactionGroup.get_or_none(
            id=param_txn_group, account=g.account, type_=param_txn_type
        )
        if txn_group is not None:
            query = query.where(models.Transaction.group == txn_group)

    pquery = PaginatedQuery(query, paginate_by=param_limit, page=param_page)

    form_filter_data = {
        "txn_types": translates.TXN_TYPES,
        "txn_groups": (
            models.TransactionGroup.select(
                models.TransactionGroup.id,
                models.TransactionGroup.name,
            )
            .where(
                (models.TransactionGroup.account == g.account)
                & (models.TransactionGroup.type_ == param_txn_type)
            )
            .order_by(models.TransactionGroup.name)
        ).dicts(),
    }
    form_filter_values = {
        "created_at_range": param_created_at_range,
    }

    form_txns_import_data = {
        "sources": [
            {"value": "Privat24", "name": "Privat24"},
            {"value": "Monobank", "name": "Monobank"},
        ],
    }

    form_txn_edit_data = {
        "txn_groups_by_type": {
            k: list(g)
            for k, g in itertools.groupby(
                sorted(
                    models.TransactionGroup.select(models.TransactionGroup)
                    .where((models.TransactionGroup.account == g.account))
                    .order_by(models.TransactionGroup.name)
                    .dicts(),
                    key=lambda txn_group: txn_group["type_"],
                ),
                key=lambda txn_group: txn_group["type_"],
            )
        }
    }

    return render_template(
        "pages/balance/transactions.html",
        form_filter_data=form_filter_data,
        form_filter_values=form_filter_values,
        form_txns_import_data=form_txns_import_data,
        form_txn_edit_data=form_txn_edit_data,
        transactions=pquery.get_object_list(),
        page=pquery.get_page(),
        page_count=pquery.get_page_count(),
        limit=param_limit,
    )


@auth.login_required
@_page_init
def replenishment():
    form_data = {
        "txn_groups": (
            models.TransactionGroup.select()
            .where(
                (models.TransactionGroup.account == g.account)
                & (models.TransactionGroup.type_ == TransactionType.REPLENISHMENT)
            )
            .dicts()
        )
    }
    return render_template("pages/balance/replenishment.html", form_data=form_data)


@auth.login_required
@_page_init
def withdrawal():
    form_data = {
        "txn_groups": (
            models.TransactionGroup.select()
            .where(
                (models.TransactionGroup.account == g.account)
                & (models.TransactionGroup.type_ == TransactionType.WITHDRAWAL)
            )
            .dicts()
        )
    }
    return render_template("pages/balance/withdrawal.html", form_data=form_data)


@auth.login_required
@_page_init
def transaction_group_limits():
    txn_group_limits = models.TransactionGroupLimit.select().where(
        models.TransactionGroupLimit.balance == g.balance
    )
    used_groups_ids = [limit.group_id for limit in txn_group_limits]

    unused_txn_groups = models.TransactionGroup.select().where(
        (models.TransactionGroup.account == g.account)
        & (models.TransactionGroup.type_ == TransactionType.WITHDRAWAL)
        & (models.TransactionGroup.id.not_in(used_groups_ids))
    )

    add_form_data = {"txn_groups": unused_txn_groups}

    return render_template(
        "pages/balance/transaction_group_limits.html",
        limits=txn_group_limits,
        add_form_data=add_form_data,
    )


@auth.login_required
@_page_init
def statistic():
    tz = app.config["TIMEZONE"]
    dt_format = constants.DATETIME_FORMAT
    utc_now = datetime.datetime.utcnow()
    local_now = dates.make_local_from_utc(utc_now, tz)
    months = [
        "Январь",
        "Февраль",
        "Март",
        "Апрель",
        "Май",
        "Июнь",
        "Июль",
        "Август",
        "Сентябрь",
        "Октябрь",
        "Ноябрь",
        "Декабрь",
    ]

    month_idx = request.args.get("month")
    if month_idx is None:
        month_idx = local_now.month
    month_idx = int(month_idx)

    local_since_dt = datetime.datetime(local_now.year, month_idx, 1)
    local_until_dt = datetime.datetime(
        (local_now.year + 1) if month_idx == 12 else local_now.year,
        1 if month_idx == 12 else month_idx + 1,
        1,
    )

    since_dt = dates.make_utc_from_dt(local_since_dt, tz)
    until_dt = dates.make_utc_from_dt(local_until_dt, tz)

    months_options = {
        idx + 1: name for idx, name in enumerate(months[: local_now.month])
    }

    today_date = local_now.strftime(constants.DATE_FORMAT)
    last_day = calendar.monthrange(local_now.year, local_now.month)[1]
    days_left = last_day - local_now.day
    days_left_pct = round(local_now.day * 100 / last_day, 2)

    date_options = {
        "today_date": today_date,
        "days_left": days_left,
        "days_left_pct": f"{days_left_pct:.2f}",
    }

    first_txn = (
        models.Transaction.select()
        .where(
            (models.Transaction.balance == g.balance)
            & (models.Transaction.created_at.between(since_dt, until_dt))
        )
        .order_by(models.Transaction.created_at)
        .first()
    )

    last_txn = (
        models.Transaction.select()
        .where(
            (models.Transaction.balance == g.balance)
            & (models.Transaction.created_at.between(since_dt, until_dt))
        )
        .order_by(models.Transaction.created_at.desc())
        .first()
    )

    replenishments = list(
        models.Transaction.select()
        .where(
            (models.Transaction.balance == g.balance)
            & (models.Transaction.type_ == TransactionType.REPLENISHMENT)
            & (models.Transaction.created_at.between(since_dt, until_dt))
        )
        .order_by(models.Transaction.created_at)
    )

    withdrawals = list(
        models.Transaction.select(models.Transaction, models.TransactionGroup)
        .join(models.TransactionGroup, pw.JOIN.LEFT_OUTER)
        .where(
            (models.Transaction.balance == g.balance)
            & (models.Transaction.type_ == TransactionType.WITHDRAWAL)
            & (models.Transaction.created_at.between(since_dt, until_dt))
        )
        .order_by(models.Transaction.created_at)
    )

    start_balance = 0
    if first_txn is not None:
        if first_txn.type_ == TransactionType.REPLENISHMENT:
            start_balance = first_txn.balance_remainder - first_txn.amount
        else:
            start_balance = first_txn.balance_remainder + first_txn.amount

    finish_balance = 0
    if last_txn is not None:
        finish_balance = last_txn.balance_remainder

    withdrawals_sum = sum(txn.amount for txn in withdrawals)
    replenishments_sum = sum(txn.amount for txn in replenishments)
    savings = start_balance - withdrawals_sum

    withdrawals_sum_pct = f"{withdrawals_sum * 100 / (start_balance or 1):.2f}"
    savings_pct = f"{savings * 100 / (start_balance or 1):.2f}"

    amount_status = {
        "start_balance": g.balance.to_amount_repr(start_balance),
        "finish_balance": g.balance.to_amount_repr(finish_balance),
        "withdrawals_sum": g.balance.to_amount_repr(withdrawals_sum),
        "withdrawals_sum_pct": withdrawals_sum_pct,
        "savings": g.balance.to_amount_repr(savings),
        "savings_pct": savings_pct,
        "replenishments_sum": g.balance.to_amount_repr(replenishments_sum),
    }

    chart_data = {}
    for txn in withdrawals:
        chart_data[txn.group] = chart_data.get(txn.group, [])
        chart_data[txn.group].append(txn)

    withdrawals_chart = []

    no_group_txns = chart_data.pop(None, None)
    if no_group_txns is not None:
        amount_sum = sum(txn.amount for txn in no_group_txns)
        to_withdrawals_sum_pct = amount_sum * 100.0 / (withdrawals_sum or 1)
        to_start_balance_pct = amount_sum * 100.0 / (start_balance or 1)
        withdrawals_chart.append(
            {
                "sort_field": to_withdrawals_sum_pct,
                "group": "Без группы",
                "color_sign": "#ddd",
                "amount_sum": g.balance.to_amount_repr(amount_sum),
                "to_withdrawals_sum_pct": f"{to_withdrawals_sum_pct:.2f}",
                "to_start_balance_pct": f"{to_start_balance_pct:.2f}",
                "type": "NOTSET",
                "group_id": "NO_GROUP",
                "limit": "",
                "limit_pct": "",
                "limit_class": "",
            }
        )

    for txn_group, txns in chart_data.items():
        amount_sum = sum(txn.amount for txn in txns)
        to_withdrawals_sum_pct = amount_sum * 100.0 / (withdrawals_sum or 1)
        to_start_balance_pct = amount_sum * 100.0 / (start_balance or 1)

        limit = ""
        limit_pct = 0
        limit_class = ""
        limit_row = (
            models.TransactionGroupLimit.select()
            .where(
                (models.TransactionGroupLimit.balance == g.balance)
                & (models.TransactionGroupLimit.group == txn_group)
            )
            .first()
        )
        if limit_row is not None:
            limit_left = limit_row.month_limit - amount_sum
            limit_pct = 100 - (limit_left * 100.0 / limit_row.month_limit)
            limit = g.balance.to_amount_repr(limit_left)
            limit_class = (
                "text-success"
                if limit_pct < 80.0
                else ("text-danger" if limit_pct >= 100.0 else "text-warning")
            )

        withdrawals_chart.append(
            {
                "sort_field": to_withdrawals_sum_pct,
                "group": txn_group.name,
                "color_sign": txn_group.color_sign,
                "amount_sum": g.balance.to_amount_repr(amount_sum),
                "to_withdrawals_sum_pct": f"{to_withdrawals_sum_pct:.2f}",
                "to_start_balance_pct": f"{to_start_balance_pct:.2f}",
                "type": txn_group.type_,
                "group_id": txn_group.id,
                "limit": limit,
                "limit_pct": f"{limit_pct:.2f}%" if limit_pct != 0 else "",
                "limit_class": limit_class,
            }
        )

    withdrawals_chart = list(
        reversed(sorted(withdrawals_chart, key=lambda data: data["sort_field"]))
    )

    form_filter_data = {
        "months_options": months_options,
    }

    form_filter_values = {
        "month": month_idx,
    }

    metadata = {
        "created_at_range": (
            f"{local_since_dt.strftime(dt_format)} - "
            f"{local_until_dt.strftime(dt_format)}"
        )
    }

    return render_template(
        "pages/balance/statistic.html",
        form_filter_data=form_filter_data,
        form_filter_values=form_filter_values,
        date_options=date_options,
        metadata=metadata,
        amount_stats=amount_status,
        withdrawals_chart=withdrawals_chart,
    )
