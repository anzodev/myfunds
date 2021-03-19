from flask import redirect
from flask import request
from flask import session
from flask import url_for

from myfunds.domain import models
from myfunds.web.tools import alerts
from myfunds.web.tools import auth


def login():
    if auth.is_authorized():
        redirect_url = session.get("last_page", url_for("page.balances"))
        return redirect(redirect_url)

    username = request.form["username"]

    account = models.Account.get_or_none(username=username)
    if account is None:
        alerts.error(f"Аккаунт {username} не найден.")
        return redirect(url_for("page.login"))

    auth.authorize_account(account)
    return redirect(url_for("page.index"))


@auth.login_required
def logout():
    auth.clear_session()
    return redirect(url_for("page.login"))
