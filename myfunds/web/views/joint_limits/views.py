import peewee as pw
from flask import Blueprint
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for

from myfunds.core.models import Account
from myfunds.core.models import Category
from myfunds.core.models import Currency
from myfunds.core.models import JointLimit
from myfunds.core.models import JointLimitParticipant
from myfunds.web import auth
from myfunds.web import notify
from myfunds.web import utils
from myfunds.web.forms import AddJointLimitForm
from myfunds.web.forms import DeleteJointLimitForm


bp = Blueprint("joint_limits", __name__, template_folder="templates")


@bp.route("/joint-limits")
@auth.login_required
@auth.superuser_required
def index():
    # fmt: off
    currencies = Currency.select().order_by(Currency.code_alpha)

    participants = (
        JointLimit
        .select(
            JointLimit.id,
            pw.fn.COUNT(
                pw.fn.DISTINCT(JointLimitParticipant.category.account.id)
            ).alias("participants"),
        )
        .join(JointLimitParticipant)
        .join(Category)
        .join(Account)
        .group_by(JointLimit.id)
    )

    limits = (
        JointLimit
        .select(
            JointLimit,
            Currency,
            pw.Value(participants.c.participants).alias("participants"),
        )
        .join(Currency)
        .switch()
        .join(
            participants,
            pw.JOIN.LEFT_OUTER,
            on=(JointLimit.id == participants.c.id)
        )
        .order_by(JointLimit.name)
    )
    # fmt: on

    return render_template(
        "joint_limits/view.html", currencies=currencies, limits=limits
    )


@bp.route("/joint-limits/new", methods=["POST"])
@auth.login_required
@auth.superuser_required
def new():
    redirect_url = url_for("joint_limits.index")

    form = AddJointLimitForm(request.form)
    utils.validate_form(form, redirect_url)

    currency_id = form.currency_id.data
    name = form.name.data
    amount = form.amount.data

    currency = Currency.get_or_none(id=currency_id)
    if currency is None:
        notify.error("Currency not found.")
        return redirect(redirect_url)

    # fmt: off
    limit_exists = (
        JointLimit
        .select(JointLimit.id)
        .where(
            (JointLimit.name == name)
        )
        .exists()
    )
    # fmt: on
    if limit_exists:
        notify.error("Limit exists already.")
        return redirect(redirect_url)

    JointLimit.create(currency=currency, name=name, amount=amount)
    notify.info("New limit was created.")

    return redirect(redirect_url)


@bp.route("/joint-limits/delete", methods=["POST"])
@auth.login_required
@auth.superuser_required
def delete():
    redirect_url = url_for("joint_limits.index")

    form = DeleteJointLimitForm(request.form)
    utils.validate_form(form, redirect_url)

    limit_id = form.limit_id.data

    limit = JointLimit.get_or_none(id=limit_id)
    if limit is None:
        notify.error("Limit not found.")
        return redirect(redirect_url)

    limit.delete_instance()
    notify.info(f"Limit '{limit.name}' was deleted.")

    return redirect(redirect_url)
