from datetime import datetime

from flask import g
from flask import render_template

from myfunds.core.models import Balance
from myfunds.core.models import CryptoBalance
from myfunds.core.models import CryptoCurrency
from myfunds.core.models import Currency
from myfunds.modules import cmc
from myfunds.modules import convertmymoney
from myfunds.web import auth
from myfunds.web import utils
from myfunds.web.constants import DATETIME_FORMAT
from myfunds.web.views.dashboard.views import bp


@bp.route("/total-budget")
@auth.login_required
def total_budget():
    common_balances = []

    balances = (
        Balance.select()
        .join(Currency)
        .where(Balance.account == g.authorized_account)
        .order_by(Balance.name)
    )

    crypto_balances = (
        CryptoBalance.select()
        .join(CryptoCurrency)
        .where(CryptoBalance.account == g.authorized_account)
        .order_by(CryptoBalance.name, CryptoCurrency.symbol)
    )

    if not balances and not common_balances:
        data = {"common_balances": common_balances, "total_amount": None}
        return render_template("total-budget.html", data=data)

    try:
        exchange_rates = convertmymoney.fetch_exchange_rates()
    except Exception as e:
        g.logger.warning(f"Unexpected error while fetching exchange rates ({repr(e)}).")
        exchange_rates = {}

    for b in balances:
        item = {}
        item["balance_name"] = b.name
        item["currency_code"] = b.currency.code_alpha
        item["amount"] = float(utils.make_hrf_amount(b.amount, b.currency.precision))

        rate = exchange_rates.get(b.currency.code_alpha)
        if rate is not None:
            item["converted_amount"] = round(item["amount"] / rate, 2)
        else:
            item["converted_amount"] = None

        common_balances.append(item)

    currencies_ids = [b.currency.cmc_id for b in crypto_balances]

    try:
        prices = cmc.fetch_prices(currencies_ids)
    except cmc.CMCError as e:
        g.logger.warning(repr(e))
        prices = {}

    for b in crypto_balances:
        item = {}
        item["balance_name"] = b.name
        item["currency_code"] = b.currency.symbol
        item["amount"] = float(utils.make_hrf_amount(b.quantity, 8))

        price = prices.get(b.currency.cmc_id)
        if price is not None:
            item["converted_amount"] = round(item["amount"] * price, 2)
        else:
            item["converted_amount"] = None

        common_balances.append(item)

    total_converted_amount = round(
        sum(
            [
                i["converted_amount"]
                for i in common_balances
                if i["converted_amount"] is not None
            ]
        ),
        2,
    )

    # fmt: off
    total_amount = (
        [f"{total_converted_amount} USD"]
        + [
            f'{i["amount"]} {i["currency_code"]}'
            for i in common_balances if i["converted_amount"] is None
        ]
    )
    # fmt: on

    total_amount = "\n+ ".join(total_amount)

    current_time = datetime.now().strftime(DATETIME_FORMAT)
    data = {"common_balances": common_balances, "total_amount": total_amount}

    return render_template("total-budget.html", current_time=current_time, data=data)
