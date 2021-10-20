from flask import g
from flask import redirect
from flask import request
from flask import url_for
from wtforms import validators as vals

from myfunds.core.models import Category
from myfunds.core.usecase.transactions import make_replenishment
from myfunds.web import auth
from myfunds.web import notify
from myfunds.web import utils
from myfunds.web.constants import FundsDirection
from myfunds.web.forms import AddTransactionForm
from myfunds.web.views.balances.balance.views import bp
from myfunds.web.views.balances.balance.views import verify_balance


@bp.route("/replenish", methods=["POST"])
@auth.login_required
@verify_balance
def replenishment():
    redirect_url = request.form.get(
        "return_url", url_for("balances.i.transactions", balance_id=g.balance.id)
    )

    form = AddTransactionForm(request.form)
    form.amount.validators.append(vals.Regexp(g.amount_pattern))
    utils.validate_form(form, redirect_url)

    amount = utils.amount_to_subunits(form.amount.data, g.currency.precision)
    category_id = form.category_id.data
    created_at = form.created_at.data
    comment = form.comment.data

    category = None
    if category_id is not None:
        category = Category.get_or_none(
            id=category_id,
            account=g.authorized_account,
            direction=FundsDirection.INCOME.value,
        )
        if category is None:
            notify.error("Category not found.")
            return redirect(redirect_url)

    make_replenishment(
        balance=g.balance,
        amount=amount,
        category=category,
        comment=comment,
        created_at=created_at,
    )
    notify.info("New replenishment was created.")

    return redirect(redirect_url)
