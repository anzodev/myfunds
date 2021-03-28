from functools import wraps

from flask import abort
from flask import g
from flask import render_template

from myfunds.domain import models
from myfunds.web.tools import auth
from myfunds.web.tools import translates


def _page_init(f):
    @wraps(f)
    def wrapper(txn_group_id: int, *args, **kwargs):
        g.txn_types = translates.TXN_TYPES
        g.txn_group = models.TransactionGroup.get_or_none(
            id=txn_group_id, account=g.account
        )
        if g.txn_group is None:
            abort(404)

        return f(*args, **kwargs)

    return wrapper


@auth.login_required
@_page_init
def edit():
    return render_template("pages/txn-group/edit.html")
