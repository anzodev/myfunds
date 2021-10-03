from flask import g
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
from wtforms import validators as vals

from myfunds.core.models import Category
from myfunds.core.usecase.transactions import make_withdrawal
from myfunds.web import auth
from myfunds.web import notify
from myfunds.web import utils
from myfunds.web.constants import FundsDirection
from myfunds.web.forms import AddTransactionForm
from myfunds.web.views.balances.balance.views import bp
from myfunds.web.views.balances.balance.views import verify_balance


@bp.route("/withdrawal", methods=["GET", "POST"])
@auth.login_required
@verify_balance
def withdrawal():
    if request.method == "GET":
        amount_pattern = utils.make_amount_pattern(g.currency.precision)
        amount_placeholder = utils.make_amount_placeholder(g.currency.precision)
        categories = (
            Category.select()
            .where(
                (Category.account == g.authorized_account)
                & (Category.direction == FundsDirection.EXPENSE.value)
            )
            .order_by(Category.name)
        )
        return render_template(
            "balance/withdrawal.html",
            amount_pattern=amount_pattern,
            amount_placeholder=amount_placeholder,
            categories=categories,
        )

    form = AddTransactionForm(request.form)
    form.amount.validators.append(
        vals.Regexp(utils.make_amount_pattern(g.currency.precision))
    )

    if not form.validate():
        notify.error("Form data validation error.")
        return redirect(url_for("balances.i.withdrawal", balance_id=g.balance.id))

    amount = utils.amount_to_subunits(form.amount.data, g.currency.precision)
    category_id = form.category_id.data
    created_at = form.created_at.data
    comment = form.comment.data

    category = None
    if category_id is not None:
        category = Category.get_or_none(
            id=category_id,
            account=g.authorized_account,
            direction=FundsDirection.EXPENSE.value,
        )
        if category is None:
            notify.error("Category not found.")
            return redirect(url_for("balances.i.withdrawal", balance_id=g.balance.id))

    make_withdrawal(
        balance=g.balance,
        amount=amount,
        category=category,
        comment=comment,
        created_at=created_at,
    )
    notify.info("New withdrawal was created.")

    return redirect(url_for("balances.i.withdrawal", balance_id=g.balance.id))
