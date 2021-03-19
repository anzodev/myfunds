from flask import redirect
from flask import request
from flask import session
from flask import url_for

from myfunds.domain import business
from myfunds.domain import models
from myfunds.web.tools import alerts
from myfunds.web.tools import auth


def add_account():
    if auth.is_authorized():
        redirect_url = session.get("last_page", url_for("page.balances"))
        return redirect(redirect_url)

    username = request.form["username"]

    account = models.Account.get_or_none(username=username)
    if account is not None:
        alerts.error(f"Аккаунт {username} уже существует.")
        return redirect(url_for("page.new_account"))

    account = business.create_account(username)
    alerts.info("Новый аккаунт успешно добавлен.")

    return redirect(url_for("page.login"))
