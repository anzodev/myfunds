from typing import List

from flask import g
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for

from myfunds.core.models import TransactionImportSettings
from myfunds.modules import txnfetcher
from myfunds.modules.api.monobank import PersonalAPI as MonobankPersonalAPI
from myfunds.modules.api.privat24 import MerchantAPI as Privat24MerchantAPI
from myfunds.web import auth
from myfunds.web import notify
from myfunds.web import utils
from myfunds.web.forms import Privat24FetcherConfigForm
from myfunds.web.views.balances.balance.views import bp
from myfunds.web.views.balances.balance.views import verify_balance


SUPPORTED_CURRENCIES = [(980, "UAH"), (840, "USD"), (978, "EUR"), (826, "GBP")]
SUPPORTED_CURRENCIES_NUM_TO_ALPHA = {n: a for n, a in SUPPORTED_CURRENCIES}
SUPPORTED_CURRENCIES_ALPHA_TO_NUM = {a: n for n, a in SUPPORTED_CURRENCIES}


@bp.route("/import-settings", methods=["GET"])
@auth.login_required
@verify_balance
def import_settings():
    settings = TransactionImportSettings.get_or_none(balance=g.balance)
    if settings is None:
        return redirect(
            url_for("balances.i.setup_import_settings", balance_id=g.balance.id)
        )

    return render_template("balance/import-settings/view.html", settings=settings)


@bp.route("/import-settings/reset", methods=["POST"])
@auth.login_required
@verify_balance
def reset_import_settings():
    redirect_url = url_for("balances.i.import_settings", balance_id=g.balance.id)

    settings = TransactionImportSettings.get_or_none(balance=g.balance)
    if settings is None:
        notify.error("Settings not found.")
        return redirect(redirect_url)

    settings.delete_instance()
    notify.info("Successfully reset import settings.")

    return redirect(redirect_url)


@bp.route("/import-settings/setup", methods=["GET", "POST"])
@auth.login_required
@verify_balance
def setup_import_settings():
    fetchers = txnfetcher.fetchers()

    if request.method == "GET":
        return render_template("balance/import-settings/setup.html", fetchers=fetchers)

    redirect_url = url_for("balances.i.setup_import_settings", balance_id=g.balance.id)

    provider_id = request.form.get("provider_id")
    if txnfetcher.get_fetcher(provider_id) is None:
        notify.error("Provider not found.")
        return redirect(redirect_url)

    return redirect(
        url_for(
            f"balances.i.setup_import_settings__{provider_id}", balance_id=g.balance.id
        )
    )


@bp.route("/import-settings/setup/privat24", methods=["GET", "POST"])
@auth.login_required
@verify_balance
def setup_import_settings__privat24():
    if request.method == "GET":
        return render_template("balance/import-settings/setup-privat24.html")

    redirect_url = url_for(
        "balances.i.setup_import_settings__privat24", balance_id=g.balance.id
    )

    settings = TransactionImportSettings.get_or_none(balance=g.balance)
    if settings is not None:
        notify.error("Provider already configured.")
        return redirect(redirect_url)

    form = Privat24FetcherConfigForm(request.form)
    utils.validate_form(form, redirect_url)

    merchant_id = form.merchant_id.data
    merchant_password = form.merchant_password.data
    card = form.card.data

    api = Privat24MerchantAPI(merchant_id, merchant_password, card)
    xml_data = api.card_info()

    currency = xml_data.find("./data/info/cardbalance/card/currency")
    if currency is None:
        notify.error("Currency not found.")
        return redirect(redirect_url)

    if currency.text != g.currency.code_alpha:
        notify.error("Current balance has another currency.")
        return redirect(redirect_url)

    TransactionImportSettings.create(
        balance=g.balance,
        provider="privat24",
        config={
            "merchant_id": merchant_id,
            "merchant_password": merchant_password,
            "card": card,
            "ccy_precision": g.currency.precision,
        },
        internal_data={"split_by_days": True, "min_interval": 0},
    )
    notify.info("Successfully setup import settings.")

    return redirect(url_for("balances.i.import_settings", balance_id=g.balance.id))


@bp.route("/import-settings/setup/monobank", methods=["GET", "POST"])
@auth.login_required
@verify_balance
def setup_import_settings__monobank():
    provider_internal_data = {
        "split_by_days": False,
        "min_interval": 60,
        "since_offset": 1,
    }

    if request.method == "GET":
        return render_template("balance/import-settings/setup-monobank.html", step=1)

    token = request.form.get("token")
    if token is None:
        notify.error("Token not found.")
        return redirect(
            url_for(
                "balances.i.setup_import_settings__monobank", balance_id=g.balance.id
            )
        )

    account = request.form.get("account")
    if account is not None:
        TransactionImportSettings.create(
            balance=g.balance,
            provider="monobank",
            config={"token": token, "account": account},
            internal_data=provider_internal_data,
        )
        notify.info("Successfully setup import settings.")

        return redirect(url_for("balances.i.import_settings", balance_id=g.balance.id))

    api = MonobankPersonalAPI(token)
    data = api.client_info()

    eligable_accounts: List[tuple] = []
    for account in data["accounts"]:
        currency_code = account["currencyCode"]
        ccy_code_alpha = SUPPORTED_CURRENCIES_NUM_TO_ALPHA.get(currency_code)
        if ccy_code_alpha is None or ccy_code_alpha != g.currency.code_alpha:
            continue

        balance = utils.make_hrf_amount(account["balance"], g.currency.precision)
        masked_pan = account.get("maskedPan")
        if masked_pan is not None and len(masked_pan) == 1:
            masked_pan = masked_pan[0]

        account_id = account["id"]
        account_repr = f"{masked_pan} ({balance} {ccy_code_alpha})"
        eligable_accounts.append((account_id, account_repr))

    if len(eligable_accounts) > 1:
        return render_template(
            "balance/import-settings/setup-monobank.html",
            step=2,
            token=token,
            eligable_accounts=eligable_accounts,
        )

    elif len(eligable_accounts) == 1:
        account = eligable_accounts[0][0]
        TransactionImportSettings.create(
            balance=g.balance,
            provider="monobank",
            config={"token": token, "account": account},
            internal_data=provider_internal_data,
        )
        notify.info("Successfully setup import settings.")

        return redirect(url_for("balances.i.import_settings", balance_id=g.balance.id))

    else:
        notify.error("We didn't find any eligable accounts.")
        return redirect(url_for("balances.i.import_settings", balance_id=g.balance.id))
