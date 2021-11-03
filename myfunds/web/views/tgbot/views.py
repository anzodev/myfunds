from flask import Blueprint
from flask import current_app
from flask import g
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for

from myfunds.core.models import TelegramBotAccount
from myfunds.modules.tg import BotClient
from myfunds.web import auth
from myfunds.web import notify
from myfunds.web import utils
from myfunds.web.forms import ResetTelegramBotAccountForm
from myfunds.web.forms import SignUpTelegramBotAccountForm


bp = Blueprint("tgbot", __name__, template_folder="templates")


@bp.route("/tgbot")
@auth.login_required
def index():
    tgbot_token = current_app.config["TGBOT_TOKEN"]
    if tgbot_token is None:
        return render_template("tgbot/view.html")

    client = BotClient(tgbot_token)
    bot = client.get_me()
    bot_username = bot["username"]

    tg_account = TelegramBotAccount.get_or_none(account=g.authorized_account)

    return render_template(
        "tgbot/view.html", bot_username=bot_username, tg_account=tg_account
    )


@bp.route("/tgbot/sign-up", methods=["POST"])
@auth.login_required
def sign_up():
    redirect_url = url_for("tgbot.index")

    form = SignUpTelegramBotAccountForm(request.form)
    utils.validate_form(form, redirect_url)

    chat_id = form.chat_id.data

    tg_account = TelegramBotAccount.get_or_none(
        account=g.authorized_account, chat_id=chat_id
    )
    if tg_account is not None:
        notify.error("Chat is signed up already.")
        return redirect(redirect_url)

    TelegramBotAccount.create(account=g.authorized_account, chat_id=chat_id)
    notify.info("New account is signed up.")

    return redirect(redirect_url)


@bp.route("/tgbot/reset", methods=["POST"])
@auth.login_required
def reset():
    redirect_url = url_for("tgbot.index")

    form = ResetTelegramBotAccountForm(request.form)
    utils.validate_form(form, redirect_url)

    chat_id = form.chat_id.data

    tg_account = TelegramBotAccount.get_or_none(
        account=g.authorized_account, chat_id=chat_id
    )
    if tg_account is None:
        notify.info("Telegram account not found.")
        return redirect(redirect_url)

    tg_account.delete_instance()
    notify.info("Successfully reset account registration.")

    return redirect(redirect_url)
