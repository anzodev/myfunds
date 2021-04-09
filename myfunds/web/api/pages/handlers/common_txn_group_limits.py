from flask import render_template

from myfunds.domain import models
from myfunds.web.tools import auth


@auth.login_required
@auth.superuser_required
def main():
    limits = (
        models.CommonTransactionGroupLimit.select()
        .join(models.Currency)
        .order_by(models.CommonTransactionGroupLimit.name)
    )
    return render_template("pages/common-txn-group-limits/main.html", limits=limits)


@auth.login_required
@auth.superuser_required
def new():
    form_data = {"currencies": models.Currency.select().dicts()}
    return render_template(
        "pages/common-txn-group-limits/new.html", form_data=form_data
    )
