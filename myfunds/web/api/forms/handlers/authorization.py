from flask import current_app
from flask import redirect
from flask import request
from flask import session
from flask import url_for

from myfunds.domain import models
from myfunds.web.tools import alerts
from myfunds.web.tools import auth
from myfunds.web.tools import password_hasher


def login():
    if auth.is_authorized():
        redirect_url = session.get("last_page", url_for("page.balances"))
        return redirect(redirect_url)

    username = request.form["username"]
    password = request.form["password"]

    url_params = {
        "username": username,
    }

    account = models.Account.get_or_none(username=username)
    if account is None:
        alerts.error("Имя пользователя или пароль не верный.")
        return redirect(url_for("page.login", **url_params))

    ph = password_hasher.PBKDF2_SHA256_PasswordHasher()
    if not ph.is_password_correct(account.password_hash, password):
        alerts.error("Имя пользователя или пароль не верный.")
        return redirect(url_for("page.login", **url_params))

    auth.authorize_account(account)

    return redirect(url_for("page.index"))


@auth.login_required
def logout():
    auth.clear_session()
    return redirect(url_for("page.login"))
