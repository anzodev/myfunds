from flask import g
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
from wtforms import validators as vals

from myfunds.core.models import Category
from myfunds.core.models import CategoryMonthLimit
from myfunds.web import auth
from myfunds.web import notify
from myfunds.web import utils
from myfunds.web.constants import FundsDirection
from myfunds.web.forms import AddExpenseLimitForm
from myfunds.web.forms import DeleteExpenseLimitForm
from myfunds.web.views.balances.balance.views import bp
from myfunds.web.views.balances.balance.views import verify_balance


@bp.route("/expense-limits", methods=["GET", "POST"])
@auth.login_required
@verify_balance
def expense_limits():
    if request.method == "GET":
        # fmt: off
        expense_month_limits = (
            CategoryMonthLimit
            .select()
            .join(Category)
            .where(
                (CategoryMonthLimit.balance == g.balance)
            )
            .order_by(CategoryMonthLimit.category.name)
        )
        # fmt: on
        used_categories_ids = [i.category_id for i in expense_month_limits]

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
            "balance/expense-limits.html",
            expense_month_limits=expense_month_limits,
            expense_categories=expense_categories,
        )

    redirect_url = url_for("balances.i.expense_limits", balance_id=g.balance.id)

    form = AddExpenseLimitForm(request.form)
    form.limit.validators.append(vals.Regexp(g.amount_pattern))
    if not form.validate():
        notify.error("Form data validation error.")
        return redirect(redirect_url)

    category_id = form.category_id.data
    limit_value = utils.amount_to_subunits(form.limit.data, g.currency.precision)

    category = Category.get_or_none(id=category_id, account=g.authorized_account)
    if category is None:
        notify.error("Category not found.")
        return redirect(redirect_url)

    # fmt: off
    limit_exists_already = (
        CategoryMonthLimit
        .select(CategoryMonthLimit.id)
        .where(
            (CategoryMonthLimit.balance == g.balance)
            & (CategoryMonthLimit.category == category)
        )
        .exists()
    )
    # fmt: on
    if limit_exists_already:
        notify.error("Limit exists already.")
        return redirect(redirect_url)

    CategoryMonthLimit.create(balance=g.balance, category=category, limit=limit_value)
    notify.info("New expense limit was added.")

    return redirect(redirect_url)


@bp.route("/expense-limits/delete", methods=["POST"])
@auth.login_required
@verify_balance
def delete_expense_limits():
    redirect_url = url_for("balances.i.expense_limits", balance_id=g.balance.id)

    form = DeleteExpenseLimitForm(request.form)
    if not form.validate():
        notify.error("Form data validation error.")
        return redirect(redirect_url)

    limit_id = form.limit_id.data

    limit = CategoryMonthLimit.get_or_none(id=limit_id, balance=g.balance)
    if limit is None:
        notify.error("Expense limit not found.")
        return redirect(redirect_url)

    limit.delete_instance()
    notify.info("Expense limit was deleted.")

    return redirect(redirect_url)
