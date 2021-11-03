import peewee as pw
from flask import g
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for

from myfunds.core.models import Account
from myfunds.core.models import Category
from myfunds.core.models import JointLimitParticipant
from myfunds.web import auth
from myfunds.web import notify
from myfunds.web import utils
from myfunds.web.constants import FundsDirection
from myfunds.web.forms import AddJointLimitParticipantStep1Form
from myfunds.web.forms import AddJointLimitParticipantStep2Form
from myfunds.web.forms import DeleteJointLimitParticipantForm
from myfunds.web.forms import JointLimitParticipantGetStepForm
from myfunds.web.views.joint_limits.limit.views import bp
from myfunds.web.views.joint_limits.limit.views import verify_limit


@bp.route("/participants")
@auth.login_required
@auth.superuser_required
@verify_limit
def participants():
    participants = (
        JointLimitParticipant.select()
        .join(Category)
        .join(Account)
        .where(JointLimitParticipant.limit == g.limit)
    )
    return render_template("limit/participants.html", participants=participants)


@bp.route("/participants/new", methods=["GET", "POST"])
@auth.login_required
@auth.superuser_required
@verify_limit
def participants_new():
    # fmt: off
    current_participants_query = (
        JointLimitParticipant
        .select()
        .join(Category)
        .where(
            (JointLimitParticipant.limit == g.limit.id)
        )
    )
    # fmt: on
    current_participants_account_ids = [
        i.category.account_id for i in current_participants_query
    ]

    if request.method == "GET":
        # fmt: off
        accounts = (
            Account
            .select(Account, pw.fn.COUNT(Category).alias("categories_count"))
            .join(Category)
            .where(
                (Account.id.not_in(current_participants_account_ids))
                & (pw.Value("categories_count") > 0)
            )
            .order_by(Account.username)
            .group_by(Account.id)
        )
        # fmt: on
        return render_template("limit/new_participant.html", step=1, accounts=accounts)

    redirect_url = url_for("joint_limits.i.participants_new", limit_id=g.limit.id)

    step_form = JointLimitParticipantGetStepForm(request.form)
    utils.validate_form(step_form, redirect_url)

    step = step_form.step.data

    if step == 1:
        form = AddJointLimitParticipantStep1Form(request.form)
        utils.validate_form(form, redirect_url)

        account_id = form.account_id.data

        account = Account.get_or_none(id=account_id)
        if account is None:
            notify.error("Account not found.")
            return redirect(redirect_url)

        if account.id in current_participants_account_ids:
            notify.error("Account is participated already.")
            return redirect(redirect_url)

        # fmt: off
        categories = (
            Category
            .select(Category)
            .where(
                (Category.account_id == account.id)
                & (Category.direction == FundsDirection.EXPENSE.value)
            )
            .order_by(Category.name)
        )
        # fmt: on

        return render_template(
            "limit/new_participant.html", step=2, account=account, categories=categories
        )

    elif step == 2:
        # fmt: off
        current_categories_query = (
            JointLimitParticipant
            .select()
            .join(Category)
            .where(
                (JointLimitParticipant.limit == g.limit.id)
            )
        )
        # fmt: on
        current_categories_ids = [i.category_id for i in current_categories_query]

        form = AddJointLimitParticipantStep2Form(request.form)
        utils.validate_form(form, redirect_url)

        account_id = form.account_id.data
        category_id = form.category_id.data

        # fmt: off
        category = (
            Category
            .select()
            .where(
                (Category.id == category_id)
                & (Category.account_id.not_in(current_participants_account_ids))
                & (Category.id.not_in(current_categories_ids))
            )
            .first()
        )
        # fmt: on
        if category is None:
            notify.error("Category not found.")
            return redirect(redirect_url)

        JointLimitParticipant.create(limit=g.limit, category=category)
        notify.info("New participant was added successfully.")

        return redirect(url_for("joint_limits.i.participants", limit_id=g.limit.id))


@bp.route("/participants/delete", methods=["POST"])
@auth.login_required
@auth.superuser_required
@verify_limit
def delete_participant():
    redirect_url = url_for("joint_limits.i.participants", limit_id=g.limit.id)

    form = DeleteJointLimitParticipantForm(request.form)
    utils.validate_form(form, redirect_url)

    participant_id = form.participant_id.data

    participant = JointLimitParticipant.get_or_none(id=participant_id, limit=g.limit)
    if participant is None:
        notify.error("Participant not found.")
        return redirect(redirect_url)

    participant.delete_instance()
    notify.info("Participant was deleted.")

    return redirect(redirect_url)
