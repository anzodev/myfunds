import csv
import io
import os
import tempfile
import uuid
from collections import namedtuple
from datetime import datetime

import peewee as pw
from flask import g
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
from flask.helpers import make_response
from wtforms import Form
from wtforms import IntegerField
from wtforms import StringField
from wtforms import validators as vals

from myfunds.core.models import Category
from myfunds.core.models import Transaction
from myfunds.core.usecase import transactions as txn_usecase
from myfunds.core.usecase.transactions import remove_transaction
from myfunds.modules import reparser
from myfunds.web import auth
from myfunds.web import notify
from myfunds.web import utils
from myfunds.web.constants import DATETIME_FORMAT
from myfunds.web.constants import DATETIME_PATTERN
from myfunds.web.constants import NO_CATEGORY_ID
from myfunds.web.constants import FundsDirection
from myfunds.web.forms import DeleteTransactionForm
from myfunds.web.forms import ImportTransactionsForm
from myfunds.web.forms import UpdateTransactionCategoryForm
from myfunds.web.forms import UpdateTransactionCommentForm
from myfunds.web.views.balances.balance.views import bp
from myfunds.web.views.balances.balance.views import verify_balance


class TransactionFilterForm(Form):
    direction = StringField(
        validators=[vals.Optional(), vals.AnyOf(FundsDirection.values())]
    )
    category_id = IntegerField(validators=[vals.Optional()])
    created_at_range_hrf = StringField(
        validators=[
            vals.Optional(),
            vals.Regexp(f"{DATETIME_PATTERN.value} - {DATETIME_PATTERN.value}"),
        ]
    )
    limit = IntegerField(validators=[vals.Optional()])
    offset = IntegerField(validators=[vals.Optional()])


TransactionFilters = namedtuple(
    "TransactionFilters",
    [
        "direction",
        "category_id",
        "categories",
        "created_at_range",
        "created_at_range_hrf",
        "limit",
        "offset",
    ],
)


def init_filters(filter_form: Form) -> TransactionFilters:
    direction = filter_form.direction.data
    category_id = filter_form.category_id.data
    created_at_range_hrf = filter_form.created_at_range_hrf.data
    limit = filter_form.limit.data or 8
    offset = filter_form.offset.data or 0

    categories = []
    if direction != "":
        categories = (
            Category.select()
            .where(
                (Category.account == g.authorized_account)
                & (Category.direction == direction)
            )
            .order_by(Category.name)
        )

    created_at_range = utils.datetime_range_from_first_month_day_to_now()
    if created_at_range_hrf != "":
        created_at_range = tuple(
            datetime.strptime(i, DATETIME_FORMAT.value)
            for i in created_at_range_hrf.split(" - ")
        )
    else:
        created_at_range_hrf = " - ".join(
            i.strftime(DATETIME_FORMAT.value) for i in created_at_range
        )

    return TransactionFilters(
        direction=direction,
        category_id=category_id,
        categories=categories,
        created_at_range=created_at_range,
        created_at_range_hrf=created_at_range_hrf,
        limit=limit,
        offset=offset,
    )


def filtered_transactions(filters: TransactionFilters) -> pw.SelectQuery:
    # fmt: off
    query = (
        Transaction
        .select(Transaction, Category)
        .join(Category, pw.JOIN.LEFT_OUTER)
        .where(
            (Transaction.balance == g.balance)
            & (Transaction.created_at.between(*filters.created_at_range))
        )
        .order_by(Transaction.created_at.desc())
    )
    # fmt: on

    if filters.direction != "":
        query = query.where(Transaction.direction == filters.direction)

    if filters.category_id is not None:
        if filters.category_id == NO_CATEGORY_ID:
            query = query.where(Transaction.category.is_null())
        else:
            category = Category.get_or_none(
                id=filters.category_id, account=g.authorized_account
            )
            if category is not None and category.direction == filters.direction:
                query = query.where(Transaction.category == category)

    return query


def paginated_transactions(
    filters: TransactionFilters, filtered_txns: pw.SelectQuery
) -> tuple[list[Transaction], bool, bool]:
    limit_plus_one = filters.limit + 1
    query = filtered_txns.offset(filters.offset).limit(limit_plus_one)

    has_prev = filters.offset > 0
    has_next = len(query) == limit_plus_one

    result = list(query)[: filters.limit]

    return result, has_prev, has_next


@bp.route("/transactions")
@auth.login_required
@verify_balance
def transactions():
    filter_form = TransactionFilterForm(request.args)
    utils.validate_form(
        filter_form,
        url_for("balances.i.transactions", balance_id=g.balance.id),
        error_notify=None,
    )

    report_parsers = reparser.get_parsers_by_currency(g.currency.code_alpha)

    filters = init_filters(filter_form)
    filtered_txns = filtered_transactions(filters)
    txns, has_prev, has_next = paginated_transactions(filters, filtered_txns)

    return render_template(
        "balance/transactions.html",
        report_parsers=report_parsers,
        txns=txns,
        filters=filters,
        has_prev=has_prev,
        has_next=has_next,
    )


@bp.route("/transactions/export/csv")
@auth.login_required
@verify_balance
def transactions_export_csv():
    filter_form = TransactionFilterForm(request.args)
    utils.validate_form(
        filter_form, url_for("balances.i.transactions", balance_id=g.balance.id)
    )

    filters = init_filters(filter_form)
    filtered_txns = filtered_transactions(filters)

    buffer = io.StringIO()
    csvwriter = csv.writer(buffer, delimiter=";", quoting=csv.QUOTE_ALL)
    csvwriter.writerow(
        ["Time", "Direction", "Category", "Amount", "Currency", "Comment"]
    )

    for i in filtered_txns.iterator():
        csvwriter.writerow(
            [
                i.created_at.strftime(DATETIME_FORMAT.value),
                FundsDirection.get(i.direction).meta["name"],
                i.category.name if i.category else "",
                utils.make_hrf_amount(i.amount, g.currency.precision),
                g.currency.code_alpha,
                i.comment,
            ]
        )

    res = make_response(buffer.getvalue())
    res.headers["Content-Disposition"] = "attachment; filename=transactions.csv"
    res.headers["Content-type"] = "text/csv"
    return res


@bp.route("/transactions/import", methods=["POST"])
@auth.login_required
@verify_balance
def transactions_import():
    redirect_url = url_for(
        "balances.i.transactions", balance_id=g.balance.id, **request.args
    )

    g.logger.info(request.form.to_dict())

    form = ImportTransactionsForm(request.form)
    utils.validate_form(form, redirect_url)

    parser_id = form.parser_id.data

    report_parser = reparser.get_parser(parser_id)
    if report_parser is None:
        notify.error("Parser not found.")
        return redirect(redirect_url)

    if "report_file" not in request.files:
        notify.error("No report file.")
        return redirect(redirect_url)

    report_file = request.files["report_file"]
    if report_file.filename == "":
        notify.error("No selected file.")
        return redirect(redirect_url)

    with tempfile.TemporaryDirectory() as tmpdir:
        filename = uuid.uuid4().hex
        filepath = os.path.join(tmpdir, filename)
        report_file.save(filepath)

        for txn in report_parser(filepath).parse():
            if reparser.is_replenishment(txn):
                func = "make_replenishment"
            elif reparser.is_withdrawal(txn):
                func = "make_withdrawal"
            else:
                continue

            getattr(txn_usecase, func)(
                balance=g.balance,
                amount=txn.amount,
                category=None,
                comment=txn.comment,
                created_at=txn.created_at,
            )

    notify.info("Transaction imported successfully")
    return redirect(redirect_url)


@bp.route("/transactions/update-category", methods=["POST"])
@auth.login_required
@verify_balance
def update_transaction_category():
    redirect_url = url_for(
        "balances.i.transactions", balance_id=g.balance.id, **request.args
    )

    form = UpdateTransactionCategoryForm(request.form)
    utils.validate_form(form, redirect_url)

    txn_id = form.txn_id.data
    category_id = form.category_id.data

    txn = Transaction.get_or_none(id=txn_id, balance=g.balance)
    if txn is None:
        notify.error("Transaction not found.")
        return redirect(redirect_url)

    category = None
    if category_id is not None:
        category = Category.get_or_none(id=category_id, account=g.authorized_account)
        if category is None:
            notify.error("Category not found.")
            return redirect(redirect_url)

        if txn.direction != category.direction:
            notify.error("Wrong category direction.")
            return redirect(redirect_url)

    Transaction.update(category=category).where(Transaction.id == txn.id).execute()
    notify.info(f"Transaction {txn.id} updated successfully.")

    return redirect(redirect_url)


@bp.route("/transactions/update-comment", methods=["POST"])
@auth.login_required
@verify_balance
def update_transaction_comment():
    redirect_url = url_for(
        "balances.i.transactions", balance_id=g.balance.id, **request.args
    )

    form = UpdateTransactionCommentForm(request.form)
    utils.validate_form(form, redirect_url)

    txn_id = form.txn_id.data
    comment = form.comment.data

    txn = Transaction.get_or_none(id=txn_id, balance=g.balance)
    if txn is None:
        notify.error("Transaction not found.")
        return redirect(redirect_url)

    Transaction.update(comment=comment).where(Transaction.id == txn.id).execute()
    notify.info(f"Transaction {txn.id} updated successfully.")

    return redirect(redirect_url)


@bp.route("/transactions/delete", methods=["POST"])
@auth.login_required
@verify_balance
def delete_transaction():
    redirect_url = url_for(
        "balances.i.transactions", balance_id=g.balance.id, **request.args
    )

    form = DeleteTransactionForm(request.form)
    utils.validate_form(form, redirect_url)

    txn_id = form.txn_id.data

    txn = Transaction.get_or_none(id=txn_id, balance=g.balance)
    if txn is None:
        notify.error("Transaction not found.")
        return redirect(redirect_url)

    remove_transaction(txn)
    notify.info(f"Transaction {txn.id} was deleted.")

    return redirect(redirect_url)
