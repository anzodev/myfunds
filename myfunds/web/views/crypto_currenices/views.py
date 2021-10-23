from flask import Blueprint
from flask import g
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for

from myfunds.core.models import CryptoCurrency
from myfunds.modules import cmc
from myfunds.web import auth
from myfunds.web import notify
from myfunds.web import utils
from myfunds.web.forms import AddCryptoCurrencyForm
from myfunds.web.forms import DeleteCryptoCurrencyForm


bp = Blueprint("crypto_currencies", __name__, template_folder="templates")


@bp.route("/crypto-currencies")
@auth.login_required
@auth.superuser_required
def index():
    currencies = CryptoCurrency.select().order_by(CryptoCurrency.name)
    return render_template("crypto_currencies/view.html", currencies=currencies)


@bp.route("/crypto-currencies/new", methods=["POST"])
@auth.login_required
@auth.superuser_required
def new():
    redirect_url = url_for("crypto_currencies.index")

    form = AddCryptoCurrencyForm(request.form)
    utils.validate_form(form, redirect_url)

    url = form.url.data

    try:
        crypto_currency = cmc.fetch_currency(url)
    except Exception:
        g.logger.exception("error while crypto currency fetching")
        notify.error("Some error was occured.")
        return redirect(redirect_url)

    currency_exists = (
        CryptoCurrency.select(CryptoCurrency.id)
        .where(CryptoCurrency.cmc_id == crypto_currency.id)
        .exists()
    )
    if currency_exists:
        notify.error("Currency exists already.")
        return redirect(redirect_url)

    currency = CryptoCurrency.create(
        symbol=crypto_currency.symbol,
        name=crypto_currency.name,
        cmc_id=crypto_currency.id,
        icon=crypto_currency.img,
    )
    notify.info(f"New crypto currency {currency.symbol} was created.")

    return redirect(redirect_url)


@bp.route("/crypto-currencies/delete", methods=["POST"])
@auth.login_required
@auth.superuser_required
def delete():
    redirect_url = url_for("crypto_currencies.index")

    form = DeleteCryptoCurrencyForm(request.form)
    utils.validate_form(form, redirect_url)

    currency_id = form.currency_id.data

    currency = CryptoCurrency.get_or_none(id=currency_id)
    if currency is None:
        notify.error("Currency not found.")
        return redirect(redirect_url)

    currency.delete_instance()
    notify.info(f"Currency {currency.symbol} was deleted.")

    return redirect(redirect_url)
