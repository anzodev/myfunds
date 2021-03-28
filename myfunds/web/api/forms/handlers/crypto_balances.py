import datetime

from flask import g
from flask import redirect
from flask import request
from flask import session
from flask import url_for

from myfunds.domain import models
from myfunds.web.tools import alerts
from myfunds.web.tools import auth


@auth.login_required
def add_crypto_balance():
    name = request.form["name"]
    symbol = request.form["symbol"]
    cmc_symbol_id = request.form.get("cmc_symbol_id") or None
    cmc_symbol_id = int(cmc_symbol_id) if cmc_symbol_id is not None else cmc_symbol_id
    amount = request.form.get("amount")
    amount = float(amount) if amount is not None else amount

    url_params = {
        "name": name,
        "symbol": symbol,
        "cmc_symbol_id": cmc_symbol_id or "",
        "amount": amount or "",
    }

    crypto_balance = models.CryptoBalance.get_or_none(
        name=name, account_id=g.account.id
    )
    if crypto_balance is not None:
        alerts.error("Баланс с таким именем уже существует.")
        return redirect(
            session.get("last_page", url_for("page.crypto_balances", **url_params))
        )

    models.CryptoBalance.create(
        account=g.account,
        name=name,
        symbol=symbol,
        cmc_symbol_id=cmc_symbol_id,
        amount=round(amount * (10 ** 8)),
        created_at=datetime.datetime.utcnow(),
    )
    alerts.success("Новый баланс успешно добавлен.")

    return redirect(url_for("page.crypto_balances"))


@auth.login_required
def update_crypto_balance():
    crypto_balance_id = request.form["crypto_balance_id"]
    name = request.form["name"]
    symbol = request.form.get("symbol")
    cmc_symbol_id = request.form.get("cmc_symbol_id") or None
    cmc_symbol_id = int(cmc_symbol_id) if cmc_symbol_id is not None else cmc_symbol_id
    amount = request.form.get("amount")
    amount = float(amount) if amount is not None else amount

    crypto_balance = models.CryptoBalance.get_or_none(
        id=crypto_balance_id, account=g.account
    )
    if crypto_balance is None:
        alerts.error(f"Баланс ({crypto_balance_id}) не найден.")
        return redirect(session.get("last_page", url_for("page.crypto_balances")))

    crypto_balance.name = name
    crypto_balance.symbol = symbol
    crypto_balance.cmc_symbol_id = cmc_symbol_id
    crypto_balance.amount = round(amount * (10 ** 8))

    print(crypto_balance.__data__)
    crypto_balance.save()

    alerts.info(f"Баланс ({crypto_balance_id}) обновлен.")

    return redirect(
        url_for("page.crypto_balance_edit", crypto_balance_id=crypto_balance.id)
    )


@auth.login_required
def delete_crypto_balance():
    crypto_balance_id = int(request.form["crypto_balance_id"])

    crypto_balance = models.CryptoBalance.get_or_none(
        id=crypto_balance_id, account=g.account
    )
    if crypto_balance is None:
        alerts.error(f"Баланс ({crypto_balance_id}) не найден.")
        return redirect(session.get("last_page", url_for("page.crypto_balances")))

    crypto_balance.delete_instance()
    alerts.info(f"Баланс ({crypto_balance_id}) удален.")

    return redirect(url_for("page.crypto_balances"))
