from functools import wraps

from flask import abort
from flask import g
from flask import render_template

from myfunds.domain import models
from myfunds.web.tools import auth


def _page_init(f):
    @wraps(f)
    def wrapper(currency_id: int, *args, **kwargs):
        g.currency = models.Currency.get_or_none(id=currency_id)
        if g.currency is None:
            abort(404)

        return f(*args, **kwargs)

    return wrapper


@auth.login_required
@_page_init
def edit():
    return render_template("pages/currency/edit.html")
