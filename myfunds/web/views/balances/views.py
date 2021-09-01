from datetime import datetime

from flask import Blueprint
from flask import g
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for

from myfunds.core.models import Balance
from myfunds.core.models import Currency
from myfunds.web import auth
from myfunds.web import notify
from myfunds.web.forms import AddBalanceForm


bp = Blueprint("balances", __name__, template_folder="templates")


@bp.route("/balances")
@auth.login_required
def index():
    # fmt: off
    balances = (
        Balance
        .select()
        .join(Currency, on=(Balance.currency_id == Currency.id))
        .where(Balance.account == g.authorized_account)
        .order_by(Balance.created_at.desc())
    )
    # fmt: on
    currencies = Currency.select().order_by(Currency.code_alpha)

    return render_template(
        "balances/view.html", balances=balances, currencies=currencies
    )


@bp.route("/balances/new", methods=["POST"])
@auth.login_required
def new():
    form = AddBalanceForm(request.form)
    if not form.validate():
        notify.error("Form data validation error.")
        return redirect(url_for("currencies.index"))

    name = form.name.data
    code_alpha = form.currency.data

    currency = Currency.get_or_none(code_alpha=code_alpha)
    if currency is None:
        notify.error("Currency not found.")
        return redirect(url_for("balances.index"))

    balance_exists = (
        Balance.select(Balance.id)
        .where((Balance.account == g.authorized_account) & (Balance.name == name))
        .exists()
    )
    if balance_exists:
        notify.error("Balance exists.")
        return redirect(url_for("balances.index"))

    balance = Balance.create(
        account=g.authorized_account,
        name=name,
        currency=currency,
        amount=0,
        created_at=datetime.now(),
    )
    notify.info(f"New balance {balance.name} was created.")

    return redirect(url_for("balances.index"))
