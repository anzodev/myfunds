from functools import wraps

from flask import abort
from flask import g
from flask import render_template

from myfunds.domain import models
from myfunds.web.tools import auth


def _page_init(f):
    @wraps(f)
    def wrapper(crypto_balance_id: int, *args, **kwargs):
        g.crypto_balance = (
            models.CryptoBalance.select()
            .where(
                (models.CryptoBalance.id == crypto_balance_id)
                & (models.CryptoBalance.account == g.account)
            )
            .first()
        )
        if g.crypto_balance is None:
            abort(404)

        return f(*args, **kwargs)

    return wrapper


@auth.login_required
@_page_init
def edit():
    return render_template("pages/crypto-balance/edit.html")
