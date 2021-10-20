from flask import Blueprint
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for

from myfunds.core.models import Balance
from myfunds.core.models import Currency
from myfunds.web import auth
from myfunds.web import notify
from myfunds.web import utils
from myfunds.web.forms import AddCurrencyForm
from myfunds.web.forms import DeleteCurrencyForm


bp = Blueprint("currencies", __name__, template_folder="templates")


@bp.route("/currencies")
@auth.login_required
@auth.superuser_required
def index():
    currencies = Currency.select().order_by(Currency.code_alpha)
    return render_template("currencies/view.html", currencies=currencies)


@bp.route("/currencies/new", methods=["POST"])
@auth.login_required
@auth.superuser_required
def new():
    redirect_url = url_for("currencies.index")

    form = AddCurrencyForm(request.form)
    utils.validate_form(form, redirect_url)

    code_alpha = form.code_alpha.data.upper()
    precision = form.precision.data

    currency = Currency.create(code_alpha=code_alpha, precision=precision)
    notify.info(f"New currency {currency.code_alpha} was created.")

    return redirect(redirect_url)


@bp.route("/currencies/delete", methods=["POST"])
@auth.login_required
@auth.superuser_required
def delete():
    redirect_url = url_for("currencies.index")

    form = DeleteCurrencyForm(request.form)
    utils.validate_form(form, redirect_url)

    currency_id = form.currency_id.data

    currency = Currency.get_or_none(id=currency_id)
    if currency is None:
        notify.error("Currency not found.")
        return redirect(redirect_url)

    is_used_by_balances = (
        Balance.select(Balance.id).where(Balance.currency == currency).exists()
    )
    if is_used_by_balances:
        notify.error(
            f"Can't remove {currency.code_alpha} currency,"
            " because some balances use it."
        )
        return redirect(redirect_url)

    currency.delete_instance()
    notify.info(f"Currency {currency.code_alpha} was deleted.")

    return redirect(redirect_url)
