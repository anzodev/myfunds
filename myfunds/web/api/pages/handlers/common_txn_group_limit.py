from functools import wraps

from flask import abort
from flask import g
from flask import render_template

from myfunds.domain import models
from myfunds.domain.constants import TransactionType
from myfunds.web.tools import auth


def _page_init(f):
    @wraps(f)
    def wrapper(limit_id: int, *args, **kwargs):
        g.limit = models.CommonTransactionGroupLimit.get_or_none(id=limit_id)
        if g.limit is None:
            abort(404)

        g.limit_currency = g.limit.currency

        return f(*args, **kwargs)

    return wrapper


@auth.login_required
@auth.superuser_required
@_page_init
def edit():
    return render_template("pages/common-txn-group-limit/edit.html")


@auth.login_required
@auth.superuser_required
@_page_init
def participants():
    participants_query = (
        models.CommonTransactionGroupLimitRelation.select()
        .join(models.Balance)
        .join(models.Account)
        .switch()
        .join(models.TransactionGroup)
        .order_by(models.Account.id)
    )

    txn_groups_query = (
        models.TransactionGroup.select()
        .join(models.Account)
        .where(models.TransactionGroup.type_ == TransactionType.WITHDRAWAL)
    )

    txn_group_options = {}
    for i in txn_groups_query:
        txn_group_options[i.account_id] = txn_group_options.get(i.account_id, [])
        txn_group_options[i.account_id].append({"id": i.id, "name": i.name})

    balances_query = (
        models.Balance.select()
        .join(models.Currency)
        .switch(models.Balance)
        .join(models.Account)
        .where(
            (models.Account.id << list(txn_group_options.keys()))
            & (models.Balance.currency == g.limit.currency)
        )
    )

    balances = list(
        sorted(
            [
                {
                    "name": f"{i.name} ({i.account.username})",
                    "id": i.id,
                    "account_id": i.account_id,
                }
                for i in balances_query
            ],
            key=lambda i: i["account_id"],
        )
    )

    add_participant_form_data = {
        "txn_group_options": txn_group_options,
        "balances": balances,
    }

    return render_template(
        "pages/common-txn-group-limit/participants.html",
        participants_query=participants_query,
        add_participant_form_data=add_participant_form_data,
    )
