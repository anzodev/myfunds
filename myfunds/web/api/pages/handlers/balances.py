import peewee as pw
from flask import g
from flask import render_template

from myfunds.domain import models
from myfunds.domain.constants import TransactionType
from myfunds.web.tools import auth


@auth.login_required
def main():
    balances = (
        models.Balance.select(
            models.Balance.id,
            models.Balance.name,
            models.Balance.amount,
            models.Balance.currency,
            models.Currency,
            pw.fn.COUNT(
                pw.Case(
                    models.Transaction.type_,
                    ((TransactionType.REPLENISHMENT, models.Transaction.id),),
                    None,
                )
            ).alias("replenishments_qty"),
            pw.fn.COUNT(
                pw.Case(
                    models.Transaction.type_,
                    ((TransactionType.WITHDRAWAL, models.Transaction.id),),
                    None,
                )
            ).alias("withdrawals_qty"),
        )
        .join(models.Currency)
        .switch()
        .join(models.Transaction, pw.JOIN.LEFT_OUTER)
        .where(models.Balance.account == g.account)
        .group_by(models.Balance.id)
        .order_by(models.Balance.name)
    )
    return render_template("pages/balances/main.html", balances=balances)


@auth.login_required
def new():
    form_data = {"currencies": models.Currency.select().dicts()}
    return render_template("pages/balances/new.html", form_data=form_data)
