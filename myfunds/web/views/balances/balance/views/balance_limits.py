from flask import g
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
from wtforms import validators as vals

from myfunds.core.models import Category
from myfunds.core.models import BalanceLimit
from myfunds.web import auth
from myfunds.web import notify
from myfunds.web import utils
from myfunds.web.constants import FundsDirection
from myfunds.web.forms import AddBalanceLimitForm
from myfunds.web.forms import DeleteBalanceLimitForm
from myfunds.web.views.balances.balance.views import bp
from myfunds.web.views.balances.balance.views import verify_balance


@bp.route("/limits", methods=["GET", "POST"])
@auth.login_required
@verify_balance
def balance_limits():
    if request.method == "GET":
        # fmt: off
        balance_limits = (
            BalanceLimit
            .select()
            .join(Category)
            .where(
                (BalanceLimit.balance == g.balance)
            )
            .order_by(BalanceLimit.category.name)
        )
        # fmt: on
        used_categories_ids = [i.category_id for i in balance_limits]

        # fmt: off
        expense_categories = (
            Category
            .select()
            .where(
                (Category.account == g.authorized_account)
                & (Category.direction == FundsDirection.EXPENSE.value)
                & (Category.id.not_in(used_categories_ids))
            )
            .order_by(Category.name)
        )
        # fmt: on

        return render_template(
            "balance/balance-limits.html",
            balance_limits=balance_limits,
            expense_categories=expense_categories,
        )

    redirect_url = url_for("balances.i.balance_limits", balance_id=g.balance.id)

    form = AddBalanceLimitForm(request.form)
    form.amount.validators.append(vals.Regexp(g.amount_pattern))
    utils.validate_form(form, redirect_url)

    category_id = form.category_id.data
    amount = utils.amount_to_subunits(form.amount.data, g.currency.precision)

    category = Category.get_or_none(
        id=category_id,
        account=g.authorized_account,
        direction=FundsDirection.EXPENSE.value,
    )
    if category is None:
        notify.error("Category not found.")
        return redirect(redirect_url)

    if category.direction != FundsDirection.EXPENSE.value:
        notify.error("Wrong category direction.")
        return redirect(redirect_url)

    # fmt: off
    limit_exists_already = (
        BalanceLimit
        .select(BalanceLimit.id)
        .where(
            (BalanceLimit.balance == g.balance)
            & (BalanceLimit.category == category)
        )
        .exists()
    )
    # fmt: on
    if limit_exists_already:
        notify.error("Limit exists already.")
        return redirect(redirect_url)

    BalanceLimit.create(balance=g.balance, category=category, amount=amount)
    notify.info("New limit was added.")

    return redirect(redirect_url)


@bp.route("/limits/delete", methods=["POST"])
@auth.login_required
@verify_balance
def delete_limit():
    redirect_url = url_for("balances.i.balance_limits", balance_id=g.balance.id)

    form = DeleteBalanceLimitForm(request.form)
    utils.validate_form(form, redirect_url)

    limit_id = form.limit_id.data

    limit = BalanceLimit.get_or_none(id=limit_id, balance=g.balance)
    if limit is None:
        notify.error("Expense limit not found.")
        return redirect(redirect_url)

    limit.delete_instance()
    notify.info("Expense limit was deleted.")

    return redirect(redirect_url)
