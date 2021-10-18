from datetime import datetime

import peewee as pw
from flask import g
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
from wtforms import Form
from wtforms import IntegerField
from wtforms import StringField
from wtforms import validators as vals

from myfunds.core.models import Category
from myfunds.core.models import Transaction
from myfunds.core.usecase.transactions import remove_transaction
from myfunds.web import auth
from myfunds.web import notify
from myfunds.web import utils
from myfunds.web.constants import DATETIME_FORMAT
from myfunds.web.constants import DATETIME_PATTERN
from myfunds.web.constants import FundsDirection
from myfunds.web.forms import DeleteTransactionForm
from myfunds.web.forms import UpdateTransactionCategoryForm
from myfunds.web.forms import UpdateTransactionCommentForm
from myfunds.web.views.balances.balance.views import bp
from myfunds.web.views.balances.balance.views import verify_balance


FILTER_ALL_DIRECTIONS = ""
FILTER_NO_CATEGORY = -1


class TransactionFilterForm(Form):
    direction = StringField(
        validators=[vals.Optional(), vals.AnyOf(FundsDirection.values())]
    )
    category_id = IntegerField(validators=[vals.Optional()])
    created_at_between = StringField(
        validators=[
            vals.Optional(),
            vals.Regexp(f"{DATETIME_PATTERN.value} - {DATETIME_PATTERN.value}"),
        ]
    )
    limit = IntegerField(validators=[vals.Optional()])
    offset = IntegerField(validators=[vals.Optional()])


@bp.route("/transactions")
@auth.login_required
@verify_balance
def transactions():
    filter_form = TransactionFilterForm(request.args)
    if not filter_form.validate():
        return redirect(url_for("balances.i.transactions", balance_id=g.balance.id))

    direction = filter_form.direction.data
    category_id = filter_form.category_id.data
    created_at_between = filter_form.created_at_between.data
    limit = filter_form.limit.data or 8
    offset = filter_form.offset.data or 0

    categories = []
    if direction != FILTER_ALL_DIRECTIONS:
        categories = (
            Category.select()
            .where(
                (Category.account == g.authorized_account)
                & (Category.direction == direction)
            )
            .order_by(Category.name)
        )

    created_at_range = utils.datetime_range_from_first_month_day_to_now()
    if created_at_between != "":
        created_at_range = (
            datetime.strptime(i, DATETIME_FORMAT.value)
            for i in created_at_between.split(" - ")
        )
    else:
        created_at_between = " - ".join(
            i.strftime(DATETIME_FORMAT.value) for i in created_at_range
        )

    filters = {
        "direction": direction,
        "category_id": category_id,
        "categories": categories,
        "created_at_between": created_at_between,
        "limit": limit,
        "offset": offset,
    }

    # fmt: off
    txns_query = (
        Transaction
        .select(Transaction, Category)
        .join(Category, pw.JOIN.LEFT_OUTER)
        .where(
            (Transaction.balance == g.balance)
            & (Transaction.created_at.between(*created_at_range))
        )
        .order_by(Transaction.created_at.desc())
    )
    # fmt: on

    if direction != FILTER_ALL_DIRECTIONS:
        txns_query = txns_query.where(Transaction.direction == direction)

    if category_id is not None:
        if category_id == FILTER_NO_CATEGORY:
            txns_query = txns_query.where(Transaction.category.is_null())
        else:
            category = Category.get_or_none(
                id=category_id, account=g.authorized_account
            )
            if category is not None and category.direction == direction:
                txns_query = txns_query.where(Transaction.category == category)
            else:
                args = request.args.to_dict()
                args.pop("category_id")
                return redirect(
                    url_for(
                        "balances.i.transactions",
                        balance_id=g.balance.id,
                        category_id=None,
                        **args,
                    )
                )

    limit_plus_one = limit + 1
    txns_query = txns_query.offset(offset).limit(limit_plus_one)

    has_prev = offset > 0
    has_next = len(txns_query) == limit_plus_one

    txns = list(txns_query)[:limit]

    expense_categories = (
        Category.select()
        .where(
            (Category.account == g.authorized_account)
            & (Category.direction == FundsDirection.EXPENSE.value)
        )
        .order_by(Category.name)
    )
    income_categories = (
        Category.select()
        .where(
            (Category.account == g.authorized_account)
            & (Category.direction == FundsDirection.INCOME.value)
        )
        .order_by(Category.name)
    )

    return render_template(
        "balance/transactions.html",
        txns=txns,
        expense_categories=expense_categories,
        income_categories=income_categories,
        filters=filters,
        has_prev=has_prev,
        has_next=has_next,
    )


@bp.route("/transactions/update-category", methods=["POST"])
@auth.login_required
@verify_balance
def update_transaction_category():
    redirect_url = url_for(
        "balances.i.transactions", balance_id=g.balance.id, **request.args
    )

    form = UpdateTransactionCategoryForm(request.form)
    if not form.validate():
        notify.error("Form data validation error.")
        return redirect()

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
    if not form.validate():
        notify.error("Form data validation error.")
        return redirect(redirect_url)

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
    if not form.validate():
        notify.error("Form data validation error.")
        return redirect(redirect_url)

    txn_id = form.txn_id.data

    txn = Transaction.get_or_none(id=txn_id, balance=g.balance)
    if txn is None:
        notify.error("Transaction not found.")
        return redirect(redirect_url)

    remove_transaction(txn)
    notify.info(f"Transaction {txn.id} was deleted.")

    return redirect(redirect_url)
