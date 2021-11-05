import csv
import io
from datetime import datetime

import peewee as pw
from flask import Blueprint
from flask import g
from flask import make_response
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
from wtforms import Form
from wtforms import IntegerField
from wtforms import validators as vals

from myfunds.core.constants import CryptoDirection
from myfunds.core.models import CryptoActionLog
from myfunds.core.models import CryptoBalance
from myfunds.core.models import CryptoCurrency
from myfunds.core.models import CryptoTransaction
from myfunds.core.models import db_proxy
from myfunds.modules import cmc
from myfunds.web import ajax
from myfunds.web import auth
from myfunds.web import notify
from myfunds.web import utils
from myfunds.web.constants import DATETIME_FORMAT
from myfunds.web.forms import AddCryptoBalanceForm
from myfunds.web.forms import AddCyptoTransactionForm
from myfunds.web.forms import DeleteCryptoBalanceForm
from myfunds.web.forms import UpdateCryptoBalanceQuantityForm


USD_CODE = "USD"
USD_PRECISION = 2
CRYPTO_PRECISION = 8


bp = Blueprint("crypto", __name__, template_folder="templates")


@bp.route("/crypto")
@auth.login_required
def index():
    currencies = CryptoCurrency.select().order_by(CryptoCurrency.symbol)

    balances = (
        CryptoBalance.select()
        .join(CryptoCurrency)
        .where(CryptoBalance.account == g.authorized_account)
        .order_by(CryptoBalance.name, CryptoCurrency.symbol)
    )

    investments = (
        CryptoTransaction.select(
            pw.fn.COUNT(CryptoTransaction.id),
            pw.fn.SUM(CryptoTransaction.amount),
        )
        .where(
            (CryptoTransaction.account == g.authorized_account)
            & (CryptoTransaction.direction == CryptoDirection.INVESTMENT)
        )
        .scalar(as_tuple=True)
    )
    if investments[1] is None:
        investments = None

    fixed_profit = (
        CryptoTransaction.select(
            pw.fn.COUNT(CryptoTransaction.id),
            pw.fn.SUM(CryptoTransaction.amount),
        )
        .where(
            (CryptoTransaction.account == g.authorized_account)
            & (CryptoTransaction.direction == CryptoDirection.FIXED_PROFIT)
        )
        .scalar(as_tuple=True)
    )
    if fixed_profit[1] is None:
        fixed_profit = None

    amount_pattern = utils.make_amount_pattern(8)

    return render_template(
        "crypto/view.html",
        currencies=currencies,
        investments=investments,
        fixed_profit=fixed_profit,
        balances=balances,
        amount_pattern=amount_pattern,
    )


@bp.route("/crypto/balances/new", methods=["POST"])
@auth.login_required
def new_balance():
    redirect_url = url_for("crypto.index")

    form = AddCryptoBalanceForm(request.form)
    utils.validate_form(form, redirect_url)

    name = form.name.data
    currency_id = form.currency_id.data

    currency = CryptoCurrency.get_or_none(id=currency_id)
    if currency is None:
        notify.error("Currency not found.")
        return redirect(redirect_url)

    balance = CryptoBalance.create(
        account=g.authorized_account,
        currency=currency,
        name=name,
        quantity=0,
    )
    notify.info(f"New balance '{balance.name}' was created.")

    return redirect(redirect_url)


@bp.route("/crypto/balances/delete", methods=["POST"])
@auth.login_required
def delete_balance():
    redirect_url = url_for("crypto.index")

    form = DeleteCryptoBalanceForm(request.form)
    utils.validate_form(form, redirect_url)

    balance_id = form.balance_id.data

    balance = CryptoBalance.get_or_none(id=balance_id, account=g.authorized_account)
    if balance is None:
        notify.error("Balance not found.")
        return redirect(redirect_url)

    balance.delete_instance()
    notify.info(f"Balance '{balance.name}' was deleted.")

    return redirect(redirect_url)


@bp.route("/crypto/balances/update-quantity", methods=["POST"])
@auth.login_required
def update_quantity():
    redirect_url = url_for("crypto.index")

    form = UpdateCryptoBalanceQuantityForm(request.form)
    form.quantity.validators.append(
        vals.Regexp(utils.make_amount_pattern(CRYPTO_PRECISION))
    )
    utils.validate_form(form, redirect_url)

    action = form.action.data
    balance_id = form.balance_id.data
    quantity = utils.amount_to_subunits(form.quantity.data, CRYPTO_PRECISION)

    balance = CryptoBalance.get_or_none(id=balance_id, account=g.authorized_account)
    if balance is None:
        notify.error("Balance not found.")
        return redirect(redirect_url)

    quantity_before = balance.quantity

    if action == "set":
        balance.quantity = quantity

    elif action == "add":
        balance.quantity += quantity

    else:
        balance.quantity -= quantity

    if balance.quantity < 0:
        notify.error("Balance quantity can't be less then zero.")
        return redirect(redirect_url)

    with db_proxy.atomic():
        CryptoActionLog.create(
            account=g.authorized_account,
            message=(
                f"{action.capitalize()} {form.quantity.data} {balance.currency.symbol} "
                f"for {balance.name} ({balance.id}), "
                f"before: {utils.make_hrf_amount(quantity_before, CRYPTO_PRECISION)}, "
                f"after: {utils.make_hrf_amount(balance.quantity, CRYPTO_PRECISION)}."
            ),
            created_at=datetime.now(),
        )
        balance.save()

    notify.info("Balance quantity was updated.")

    return redirect(redirect_url)


@bp.route("/crypto/invest", methods=["POST"])
@auth.login_required
def invest():
    redirect_url = url_for("crypto.index")

    quantity_validator = vals.Regexp(utils.make_amount_pattern(CRYPTO_PRECISION))
    price_validator = vals.Regexp(utils.make_amount_pattern(USD_PRECISION))

    form = AddCyptoTransactionForm(request.form)
    form.quantity.validators.append(quantity_validator)
    form.price.validators.append(price_validator)
    utils.validate_form(form, redirect_url)

    currency_id = form.currency_id.data
    quantity = form.quantity.data
    price = form.price.data

    amount = round(float(quantity) * float(price), USD_PRECISION)

    currency = CryptoCurrency.get_or_none(id=currency_id)
    if currency is None:
        notify.error("Currency not found.")
        return redirect(redirect_url)

    with db_proxy.atomic():
        creation_time = datetime.now()

        CryptoTransaction.create(
            account=g.authorized_account,
            direction=CryptoDirection.INVESTMENT,
            symbol=currency.symbol,
            quantity=utils.amount_to_subunits(quantity, CRYPTO_PRECISION),
            price=utils.amount_to_subunits(price, USD_PRECISION),
            amount=utils.amount_to_subunits(amount, USD_PRECISION),
            created_at=creation_time,
        )

        CryptoActionLog.create(
            account=g.authorized_account,
            message=(
                f"Invest ${amount}, bought {quantity} {currency.symbol} by ${price}."
            ),
            created_at=creation_time,
        )

    notify.info("New investment was added.")

    return redirect(redirect_url)


@bp.route("/crypto/fix-profit", methods=["POST"])
@auth.login_required
def fix_profit():
    redirect_url = url_for("crypto.index")

    quantity_validator = vals.Regexp(utils.make_amount_pattern(CRYPTO_PRECISION))
    price_validator = vals.Regexp(utils.make_amount_pattern(USD_PRECISION))

    form = AddCyptoTransactionForm(request.form)
    form.quantity.validators.append(quantity_validator)
    form.price.validators.append(price_validator)
    utils.validate_form(form, redirect_url)

    currency_id = form.currency_id.data
    quantity = form.quantity.data
    price = form.price.data

    amount = round(float(quantity) * float(price), USD_PRECISION)

    currency = CryptoCurrency.get_or_none(id=currency_id)
    if currency is None:
        notify.error("Currency not found.")
        return redirect(redirect_url)

    with db_proxy.atomic():
        creation_time = datetime.now()

        CryptoTransaction.create(
            account=g.authorized_account,
            direction=CryptoDirection.FIXED_PROFIT,
            symbol=currency.symbol,
            quantity=utils.amount_to_subunits(quantity, CRYPTO_PRECISION),
            price=utils.amount_to_subunits(price, USD_PRECISION),
            amount=utils.amount_to_subunits(amount, USD_PRECISION),
            created_at=creation_time,
        )

        CryptoActionLog.create(
            account=g.authorized_account,
            message=(
                f"Fix profit ${amount}, sell {quantity} {currency.symbol} by ${price}."
            ),
            created_at=creation_time,
        )

    notify.info("New profit fix was added.")

    return redirect(redirect_url)


@bp.route("/ajax/balances-values")
@ajax.ajax_endpoint
@auth.login_required
def ajax_balances_values():
    balances = (
        CryptoBalance.select()
        .join(CryptoCurrency)
        .where(CryptoBalance.account == g.authorized_account)
    )
    currencies_ids = [i.currency.cmc_id for i in balances]

    prices = cmc.fetch_prices(currencies_ids, USD_CODE)

    data = {}
    for b in balances:
        price, amount = prices.get(b.currency.cmc_id), None
        if price is not None:
            amount = round(
                float(utils.make_hrf_amount(b.quantity, CRYPTO_PRECISION)) * price,
                USD_PRECISION,
            )

        data[int(b.id)] = {"price": price, "amount": amount}

    return data


class ActionsFilterForm(Form):
    offset = IntegerField(validators=[vals.Optional()])
    limit = IntegerField(validators=[vals.Optional()])


@bp.route("/crypto/actions")
@auth.login_required
def actions():
    filter_form = ActionsFilterForm(request.args)
    utils.validate_form(filter_form, url_for("crypto.actions"), error_notify=None)

    offset = filter_form.offset.data or 0
    limit = filter_form.limit.data or 10

    filters = {"offset": offset, "limit": limit}

    limit_plus_one = limit + 1
    query = (
        CryptoActionLog.select()
        .where(CryptoActionLog.account == g.authorized_account)
        .order_by(CryptoActionLog.created_at.desc())
        .offset(offset)
        .limit(limit_plus_one)
    )

    actions = list(query)[:limit]

    has_prev = offset > 0
    has_next = len(query) == limit_plus_one

    return render_template(
        "crypto/actions.html",
        filters=filters,
        actions=actions,
        has_prev=has_prev,
        has_next=has_next,
    )


@bp.route("/crypto/actions/export")
@auth.login_required
def export_actions():
    actions = (
        CryptoActionLog.select()
        .where(CryptoActionLog.account == g.authorized_account)
        .order_by(CryptoActionLog.created_at.desc())
    )

    buffer = io.StringIO()
    csvwriter = csv.writer(buffer, delimiter=";", quoting=csv.QUOTE_ALL)
    csvwriter.writerow(["Time", "Message"])

    for i in actions.iterator():
        csvwriter.writerow([i.created_at.strftime(DATETIME_FORMAT), i.message])

    res = make_response(buffer.getvalue())
    res.headers["Content-Disposition"] = "attachment; filename=actions.csv"
    res.headers["Content-type"] = "text/csv"
    return res
