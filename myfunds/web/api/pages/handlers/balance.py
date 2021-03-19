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

    _logger.debug(f"since_dt={since_dt}, until_dt={until_dt}")

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
    # print(
    #     list(
    #         (
    #             models.TransactionGroup.select(models.TransactionGroup)
    #             .where((models.TransactionGroup.account == g.account))
    #             .order_by(models.TransactionGroup.name)
    #         ).dicts()
    #     )
    # )
    print(form_txn_edit_data)

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
def statistic():
    tz = app.config["TIMEZONE"]
    dt_format = constants.DATETIME_FORMAT

    param_txn_type = request.args.get("txn_type", TransactionType.WITHDRAWAL)
    param_stats_range = request.args.get("stats_range")

    if param_stats_range is None:
        since_dt, until_dt = dates.make_local_range_since_first_month_day_to_now(tz)
        param_stats_range = " - ".join(
            [since_dt.strftime(dt_format), until_dt.strftime(dt_format)]
        )

    try:
        since_dt_str, until_dt_str = param_stats_range.split(" - ")
        since_dt = dates.make_utc_from_dt_str(since_dt_str, dt_format, tz)
        until_dt = dates.make_utc_from_dt_str(until_dt_str, dt_format, tz)
    except Exception:
        param_stats_range = None

    total_amount = 0

    # fmt: off
    total_amount_row = (
        models.Transaction
        .select(
            pw.fn.SUM(models.Transaction.amount).alias("total_amount"),
        )
        .where(
            (models.Transaction.balance == g.balance)
            & (models.Transaction.created_at.between(since_dt, until_dt))
            & (models.Transaction.type_ == param_txn_type)
        )
        .group_by(models.Transaction.type_)
    ).first()
    # fmt: on

    if total_amount_row is not None:
        total_amount = total_amount_row.total_amount

    query = (
        models.Transaction.select(
            models.Transaction.group,
            pw.fn.SUM(models.Transaction.amount).alias("amount_sum"),
            pw.SQL(f"round(sum(amount) * 100.0 / {total_amount}, 2)").alias(
                "amount_pct"
            ),
            models.TransactionGroup,
        )
        .join(models.TransactionGroup, pw.JOIN.LEFT_OUTER)
        .switch(models.Transaction)
        .where(
            (models.Transaction.balance == g.balance)
            & (models.Transaction.type_ == param_txn_type)
            & (models.Transaction.created_at.between(since_dt, until_dt))
        )
        .group_by(models.Transaction.group)
        .order_by(pw.SQL("amount_pct").desc())
    )

    ccy_base = g.balance.currency.base

    txns_by_groups = []
    for i in query:
        if i.group is None:
            txns_by_groups.append(
                {
                    "group": "Без группы",
                    "color_sign": "#ddd",
                    "amount_sum": f"{i.amount_sum / (10 ** ccy_base):.{ccy_base}f}",
                    "amount_pct": i.amount_pct,
                    "type": "NOTSET",
                    "group_id": "NO_GROUP",
                }
            )
            continue

        txns_by_groups.append(
            {
                "group": i.group.name,
                "color_sign": i.group.color_sign,
                "amount_sum": f"{i.amount_sum / (10 ** ccy_base):.{ccy_base}f}",
                "amount_pct": i.amount_pct,
                "type": i.group.type_,
                "group_id": i.group.id,
            }
        )

    form_filter_values = {
        "stats_range": param_stats_range,
    }

    return render_template(
        "pages/balance/statistic.html",
        form_filter_values=form_filter_values,
        txns_by_groups=txns_by_groups,
    )

    # txns_with_group = (
    #     models.Transaction.select(
    #         pw.fn.SUM(models.Transaction.amount).alias("total"),
    #         models.TransactionGroup.id,
    #         models.TransactionGroup.name,
    #         models.TransactionGroup.color,
    #     )
    #     .join(models.TransactionGroup)
    #     .where(
    #         (models.Transaction.balance == g.balance)
    #         & (models.Transaction.type_ == TransactionType.WITHDRAWAL)
    #         & (models.Transaction.created_at.between(since_dt, until_dt))
    #     )
    #     .group_by(models.TransactionGroup.id)
    # )

    # row_total_of_txns_without_groups = (
    #     models.Transaction.select(pw.fn.SUM(models.Transaction.amount).alias("total"))
    #     .where(
    #         (models.Transaction.balance == g.balance)
    #         & (models.Transaction.type_ == TransactionType.WITHDRAWAL)
    #         & (models.Transaction.group.is_null())
    #         & (models.Transaction.created_at.between(since_dt, until_dt))
    #     )
    #     .group_by(models.Transaction.group)
    #     .first()
    # )

    # form_filter_values = {"stats_range": param_stats_range}

    # chart_data = {
    #     "txn_group_ids": [],
    #     "labels": [],
    #     "background_colors": [],
    #     "data": [],
    # }

    # for txn in txns_with_group:
    #     chart_data["txn_group_ids"].append(txn.group.id)
    #     chart_data["labels"].append(txn.group.name)
    #     chart_data["background_colors"].append(txn.group.color)
    #     chart_data["data"].append(round(txn.total, 2))

    # if row_total_of_txns_without_groups is not None:
    #     chart_data["txn_group_ids"].append("NO_GROUP")
    #     chart_data["labels"].append("Без группы")
    #     chart_data["background_colors"].append("#dddddd")
    #     chart_data["data"].append(round(row_total_of_txns_without_groups.total, 2))


# @auth.login_required
# @_page_init
# def stats_total():
#     tz = app.config["TIMEZONE"]
#     dt_format = constants.DATETIME_FORMAT

#     param_stats_range = request.args.get("stats_range")

#     if param_stats_range is None:
#         since_dt, until_dt = dates.make_local_range_since_first_month_day_to_now(tz)
#         param_stats_range = " - ".join(
#             [since_dt.strftime(dt_format), until_dt.strftime(dt_format)]
#         )

#     try:
#         since_dt_str, until_dt_str = param_stats_range.split(" - ")
#         since_dt = dates.make_utc_from_dt_str(since_dt_str, dt_format, tz)
#         until_dt = dates.make_utc_from_dt_str(until_dt_str, dt_format, tz)
#     except Exception:
#         param_stats_range = None

# txns_with_group = (
#     models.Transaction.select(
#         pw.fn.SUM(models.Transaction.amount).alias("total"),
#         models.TransactionGroup.id,
#         models.TransactionGroup.name,
#         models.TransactionGroup.color,
#     )
#     .join(models.TransactionGroup)
#     .where(
#         (models.Transaction.balance == g.balance)
#         & (models.Transaction.type_ == TransactionType.WITHDRAWAL)
#         & (models.Transaction.created_at.between(since_dt, until_dt))
#     )
#     .group_by(models.TransactionGroup.id)
# )

# row_total_of_txns_without_groups = (
#     models.Transaction.select(pw.fn.SUM(models.Transaction.amount).alias("total"))
#     .where(
#         (models.Transaction.balance == g.balance)
#         & (models.Transaction.type_ == TransactionType.WITHDRAWAL)
#         & (models.Transaction.group.is_null())
#         & (models.Transaction.created_at.between(since_dt, until_dt))
#     )
#     .group_by(models.Transaction.group)
#     .first()
# )

# form_filter_values = {"stats_range": param_stats_range}

# chart_data = {
#     "txn_group_ids": [],
#     "labels": [],
#     "background_colors": [],
#     "data": [],
# }

# for txn in txns_with_group:
#     chart_data["txn_group_ids"].append(txn.group.id)
#     chart_data["labels"].append(txn.group.name)
#     chart_data["background_colors"].append(txn.group.color)
#     chart_data["data"].append(round(txn.total, 2))

# if row_total_of_txns_without_groups is not None:
#     chart_data["txn_group_ids"].append("NO_GROUP")
#     chart_data["labels"].append("Без группы")
#     chart_data["background_colors"].append("#dddddd")
#     chart_data["data"].append(round(row_total_of_txns_without_groups.total, 2))

#     return render_template(
#         "pages/balance/stats_total.html",
#         form_filter_values=form_filter_values,
#         chart_data=chart_data,
#     )


# @auth.login_required
# @_page_init
# def stats_txns():
#     tz = app.config["TIMEZONE"]
#     dt_format = constants.DATETIME_FORMAT

#     param_stats_range = request.args.get("stats_range")

#     if param_stats_range is None:
#         since_dt, until_dt = dates.make_local_range_since_first_month_day_to_now(tz)
#         param_stats_range = " - ".join(
#             [since_dt.strftime(dt_format), until_dt.strftime(dt_format)]
#         )

#     try:
#         since_dt_str, until_dt_str = param_stats_range.split(" - ")
#         since_dt = dates.make_utc_from_dt_str(since_dt_str, dt_format, tz)
#         until_dt = dates.make_utc_from_dt_str(until_dt_str, dt_format, tz)
#     except Exception:
#         param_stats_range = None

#     query = (
#         models.Transaction.select(models.Transaction, models.TransactionGroup)
#         .join(models.TransactionGroup, pw.JOIN.LEFT_OUTER)
#         .where(
#             (models.Transaction.balance == g.balance)
#             & (models.Transaction.created_at.between(since_dt, until_dt))
#         )
#     )

#     form_filter_values = {"stats_range": param_stats_range}

#     chart_data = {
#         "datasets": {},
#         "ticks_min": since_dt_str,
#         "ticks_max": until_dt_str,
#         "balance_currency": g.balance.currency.code_alpha,
#     }

#     for txn in query.iterator():
#         if txn.group is not None:
#             dataset = chart_data["datasets"].get(str(txn.group_id))
#             if dataset is None:
#                 dataset = {
#                     "label": txn.group.name,
#                     "color": txn.group.color,
#                     "data": [],
#                 }
#                 chart_data["datasets"][str(txn.group_id)] = dataset
#             dataset["data"].append(
#                 {
#                     "x": dates.make_local_from_utc(txn.created_at, tz).strftime(
#                         constants.DATETIME_FORMAT
#                     ),
#                     "y": (
#                         -txn.amount
#                         if txn.type_ == TransactionType.WITHDRAWAL
#                         else txn.amount
#                     ),
#                     "comment": txn.comment or "-",
#                 }
#             )

#         else:
#             dataset = chart_data["datasets"].get("OTHER")
#             if dataset is None:
#                 dataset = {
#                     "label": "Other",
#                     "color": "#999999",
#                     "data": [],
#                 }
#                 chart_data["datasets"]["OTHER"] = dataset
#             dataset["data"].append(
#                 {
#                     "x": dates.make_local_from_utc(txn.created_at, tz).strftime(
#                         constants.DATETIME_FORMAT
#                     ),
#                     "y": (
#                         -txn.amount
#                         if txn.type_ == TransactionType.WITHDRAWAL
#                         else txn.amount
#                     ),
#                     "comment": txn.comment or "-",
#                 }
#             )

#     return render_template(
#         "pages/balance/stats_txns.html",
#         form_filter_values=form_filter_values,
#         chart_data=chart_data,
#     )
