import peewee as pw
from flask import g
from flask import render_template

from myfunds.domain import models
from myfunds.web.tools import auth


@auth.login_required
def main():
    currencies = models.Currency.select(models.Currency).order_by(
        models.Currency.code_alpha
    )
    return render_template("pages/currencies/main.html", currencies=currencies)


@auth.login_required
def new():
    return render_template("pages/currencies/new.html")
