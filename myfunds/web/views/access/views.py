from flask import Blueprint
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for

from myfunds.core.models import Account
from myfunds.web import auth
from myfunds.web import notify
from myfunds.web import utils
from myfunds.web.app_runtime_utils import init_password_hasher
from myfunds.web.forms import LoginForm


bp = Blueprint("access", __name__, template_folder="templates")


@bp.route("/login", methods=["GET", "POST"])
def login():
    if auth.session_has_account_id():
        return redirect(url_for("general.index"))

    if request.method == "GET":
        return render_template("access/login.html")

    redirect_url = url_for("access.login")

    form = LoginForm(request.form)
    utils.validate_form(form, redirect_url)

    username = form.username.data
    password = form.password.data

    account = Account.get_or_none(username=username)
    if account is None:
        notify.error("Account not found.")
        return redirect(redirect_url)

    password_hasher = init_password_hasher()
    if not password_hasher.is_hash_correct(account.password_hash, password):
        notify.error("Wrong password.")
        return redirect(redirect_url)

    auth.authorize_account(account)

    return redirect(url_for("general.index"))


@bp.route("/logout", methods=["POST"])
@auth.login_required
def logout():
    auth.forget_account()
    return redirect(url_for("access.login"))
