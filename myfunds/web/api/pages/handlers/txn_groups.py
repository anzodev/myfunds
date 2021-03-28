import peewee as pw
from flask import g
from flask import render_template

from myfunds.domain import models
from myfunds.domain.constants import TransactionType
from myfunds.web.tools import auth
from myfunds.web.tools import translates


@auth.login_required
def main():
    txn_groups = (
        models.TransactionGroup.select(
            models.TransactionGroup.id,
            pw.Case(
                models.TransactionGroup.type_,
                (
                    (TransactionType.REPLENISHMENT, translates.TXN_TYPE_REPLENISHMENT),
                    (TransactionType.WITHDRAWAL, translates.TXN_TYPE_WITHDRAWAL),
                ),
                translates.N_A,
            ).alias("type_alias"),
            models.TransactionGroup.name,
            models.TransactionGroup.color_sign,
        )
        .where(models.TransactionGroup.account == g.account)
        .order_by(models.TransactionGroup.type_, models.TransactionGroup.name)
    )
    return render_template("pages/txn-groups/main.html", txn_groups=txn_groups)


@auth.login_required
def new():
    form_data = {"txn_types": translates.TXN_TYPES}
    return render_template("pages/txn-groups/new.html", form_data=form_data)
