from flask import g
from flask import redirect
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


@bp.route("/withdraw", methods=["POST"])
@auth.login_required
@verify_balance
def withdrawal():
    redirect_url = request.form.get(
        "return_url", url_for("balances.i.transactions", balance_id=g.balance.id)
    )

    form = AddTransactionForm(request.form)
    form.amount.validators.append(vals.Regexp(g.amount_pattern))

    if not form.validate():
        notify.error("Form data validation error.")
        return redirect(redirect_url)

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
            return redirect(redirect_url)

    make_withdrawal(
        balance=g.balance,
        amount=amount,
        category=category,
        comment=comment,
        created_at=created_at,
    )
    notify.info("New withdrawal was created.")

    return redirect(redirect_url)
