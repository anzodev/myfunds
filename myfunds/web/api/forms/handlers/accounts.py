import datetime
import ipaddress

from flask import current_app
from flask import g
from flask import redirect
from flask import request
from flask import session
from flask import url_for

from myfunds.domain import models
from myfunds.web.tools import alerts
from myfunds.web.tools import auth
from myfunds.web.tools import password_hasher


def add_account():
    if auth.is_authorized():
        redirect_url = session.get("last_page", url_for("page.balances"))
        return redirect(redirect_url)

    username = request.form["username"]
    password = request.form["password"]
    password_copy = request.form["password_copy"]

    url_params = {"username": username}

    if len(username) == 0:
        raise ValueError("Invalid username value.")

    account = models.Account.get_or_none(username=username)
    if account is not None:
        alerts.error(f"Аккаунт {username} уже существует.")
        return redirect(url_for("page.new_account", **url_params))

    if password != password_copy:
        alerts.error("Пароли не совпадают.")
        return redirect(url_for("page.new_account", **url_params))

    ph = password_hasher.PBKDF2_SHA256_PasswordHasher()
    password_hash = ph.make_hash(
        password=password,
        iterations=current_app.config["PH_ITERATIONS"],
        salt_length=current_app.config["PH_SALT_LENGTH"],
    )

    models.Account.create(
        username=username,
        password_hash=password_hash,
        created_at=datetime.datetime.utcnow(),
    )

    alerts.info("Новый аккаунт успешно добавлен.")

    return redirect(url_for("page.login"))


@auth.login_required
def update_password():
    current_password = request.form["current_password"]
    new_password = request.form["new_password"]
    password_copy = request.form["password_copy"]

    ph = password_hasher.PBKDF2_SHA256_PasswordHasher()
    if not ph.is_password_correct(g.account.password_hash, current_password):
        alerts.error("Текущий пароль указан не верно.")
        return redirect(session.get("last_page", url_for("page.account_edit")))

    if new_password != password_copy:
        alerts.error("Пароли не совпадают.")
        return redirect(session.get("last_page", url_for("page.account_edit")))

    password_hash = ph.make_hash(
        password=new_password,
        iterations=current_app.config["PH_ITERATIONS"],
        salt_length=current_app.config["PH_SALT_LENGTH"],
    )

    g.account.password_hash = password_hash
    g.account.save()

    alerts.info("Пароль успешно обновлен.")

    return redirect(session.get("last_page", url_for("page.account_edit")))


@auth.login_required
def update_ip_whitelist():
    ip_whitelist = request.form["ip_whitelist"]
    ips = ip_whitelist.split(";")

    for ip in ips:
        try:
            ipaddress.ip_address(ip)
        except ValueError:
            alerts.error("Некорректное значение белого списка.")
            return redirect(
                session.get("last_page", url_for("page.account_edit"))
            )

    g.account.ip_whitelist = ips
    g.account.save()

    alerts.info("Белый список успешно обновлен.")

    return redirect(session.get("last_page", url_for("page.account_edit")))
