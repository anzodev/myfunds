from flask import Blueprint
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for

from myfunds.core.models import Balance
from myfunds.core.models import Currency
from myfunds.web import auth
from myfunds.web import notify
from myfunds.web.forms import AddCurrencyForm
from myfunds.web.forms import DeleteCurrencyForm


bp = Blueprint("currencies", __name__, template_folder="templates")


@bp.route("/currencies")
@auth.login_required
@auth.superuser_required
def index():
    currencies = Currency.select().order_by(Currency.code_alpha)
    return render_template(
        "currencies/view.html",
        currencies=currencies,
    )


@bp.route("/currencies/new", methods=["POST"])
@auth.login_required
@auth.superuser_required
def new():
    form = AddCurrencyForm(request.form)
    if not form.validate():
        notify.error("Form data validation error.")
        return redirect(url_for("currencies.index"))

    code_alpha = form.code_alpha.data.upper()
    precision = form.precision.data

    currency = Currency.create(code_alpha=code_alpha, precision=precision)
    notify.info(f"New currency {currency.code_alpha} was created.")

    return redirect(url_for("currencies.index"))


@bp.route("/currencies/delete", methods=["POST"])
@auth.login_required
@auth.superuser_required
def delete():
    form = DeleteCurrencyForm(request.form)
    if not form.validate():
        notify.error("Form data validation error.")
        return redirect(url_for("currencies.index"))

    currency_id = form.currency_id.data

    currency = Currency.get_or_none(id=currency_id)
    if currency is None:
        notify.error("Currency not found.")
        return redirect(url_for("currencies.index"))

    is_used_by_balances = (
        Balance.select(Balance.id).where(Balance.currency == currency).exists()
    )
    if is_used_by_balances:
        notify.error(
            f"Can't remove {currency.code_alpha} currency,"
            " because some balances use it."
        )
        return redirect(url_for("currencies.index"))

    currency.delete_instance()
    notify.info(f"Currency {currency.code_alpha} was deleted.")

    return redirect(url_for("currencies.index"))
