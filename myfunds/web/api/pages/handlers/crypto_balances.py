from flask import g
from flask import render_template

from myfunds.domain import models
from myfunds.web.tools import auth


@auth.login_required
def main():
    crypto_balances = (
        models.CryptoBalance.select(models.CryptoBalance)
        .where(models.CryptoBalance.account == g.account)
        .order_by(models.CryptoBalance.amount_usd.desc())
    )

    return render_template(
        "pages/crypto-balances/main.html",
        crypto_balances=crypto_balances,
    )


@auth.login_required
def new():
    return render_template("pages/crypto-balances/new.html")
