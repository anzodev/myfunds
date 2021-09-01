from flask import Blueprint
from flask import current_app
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for

from myfunds.core.models import Account
from myfunds.web import auth
from myfunds.web import notify
from myfunds.web.app_runtime_utils import init_password_hasher
from myfunds.web.forms import AddAccountForm
from myfunds.web.forms import DeleteAccountForm
from myfunds.web.forms import UpdateAccountPasswordForm


bp = Blueprint("accounts", __name__, template_folder="templates")


@bp.route("/accounts")
@auth.login_required
@auth.superuser_required
def index():
    accounts = Account.select().order_by(Account.username)
    return render_template("accounts/view.html", accounts=accounts)


@bp.route("/accounts/new", methods=["POST"])
@auth.login_required
@auth.superuser_required
def new():
    form = AddAccountForm(request.form)
    if not form.validate():
        notify.error("Form data validation error.")
        return redirect(url_for("accounts.index"))

    username = form.username.data
    password = form.password.data

    account_exists = (
        Account.select(Account.id).where(Account.username == username).exists()
    )
    if account_exists:
        notify.error(f"Account {username} exists.")
        return redirect(url_for("accounts.index"))

    password_hasher = init_password_hasher()

    account = Account.create(
        username=username,
        password_hash=password_hasher.make_hash(password),
    )
    notify.info(f"New account {account.username} was created.")

    return redirect(url_for("accounts.index"))


@bp.route("/accounts/delete", methods=["POST"])
@auth.login_required
@auth.superuser_required
def delete():
    form = DeleteAccountForm(request.form)
    if not form.validate():
        notify.error("Form data validation error.")
        return redirect(url_for("accounts.index"))

    account_id = form.account_id.data

    account = Account.get_or_none(id=account_id)
    if account is None:
        notify.error("Account not found.")
        return redirect(url_for("accounts.index"))

    if account.username == current_app.config["SUPERUSER"]:
        notify.error("Can't remove superuser.")
        return redirect(url_for("accounts.index"))

    account.delete_instance(recursive=True)
    notify.info(f"Account {account.username} was deleted.")

    return redirect(url_for("accounts.index"))


@bp.route("/accounts/update_password", methods=["POST"])
@auth.login_required
@auth.superuser_required
def update_password():
    form = UpdateAccountPasswordForm(request.form)
    if not form.validate():
        notify.error("Form data validation error.")
        return redirect(url_for("accounts.index"))

    account_id = form.account_id.data
    old_password = form.old_password.data
    new_password = form.new_password.data

    account = Account.get_or_none(id=account_id)
    if account is None:
        notify.error("Account not found.")
        return redirect(url_for("accounts.index"))

    password_hasher = init_password_hasher()

    if not password_hasher.is_hash_correct(account.password_hash, old_password):
        notify.error("Old password missmatch.")
        return redirect(url_for("accounts.index"))

    account.password_hash = password_hasher.make_hash(new_password)
    account.save()
    notify.info("Password was updated.")
    return redirect(url_for("accounts.index"))
