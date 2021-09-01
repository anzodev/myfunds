from flask import Blueprint
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for

from myfunds.core.models import Account
from myfunds.web import auth
from myfunds.web import notify
from myfunds.web.app_runtime_utils import init_password_hasher
from myfunds.web.forms import LoginForm


bp = Blueprint("access", __name__, template_folder="templates")


@bp.route("/login", methods=["GET", "POST"])
def login():
    if auth.session_has_account_id():
        return redirect(url_for("general.index"))

    if request.method == "GET":
        return render_template("access/login.html")

    form = LoginForm(request.form)
    if not form.validate():
        notify.error("Form data validation error.")
        return redirect(url_for("access.login"))

    username = form.username.data
    password = form.password.data

    account = Account.get_or_none(username=username)
    if account is None:
        notify.error("Account not found.")
        return redirect(url_for("access.login"))

    password_hasher = init_password_hasher()
    if not password_hasher.is_hash_correct(account.password_hash, password):
        notify.error("Wrong password.")
        return redirect(url_for("access.login"))

    auth.authorize_account(account)

    return redirect(url_for("general.index"))


@bp.route("/logout", methods=["POST"])
@auth.login_required
def logout():
    auth.forget_account()
    return redirect(url_for("access.login"))
