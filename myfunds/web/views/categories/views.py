from flask import Blueprint
from flask import g
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for

from myfunds.core.models import Category
from myfunds.web import auth
from myfunds.web import notify
from myfunds.web import utils
from myfunds.web.constants import FundsDirection
from myfunds.web.forms import AddCategoryForm
from myfunds.web.forms import DeleteCategoryForm
from myfunds.web.forms import EditCategoryForm


bp = Blueprint("categories", __name__, template_folder="templates")


@bp.route("/categories")
@auth.login_required
def index():
    # fmt: off
    expense_categories = (
        Category
        .select()
        .where(
            (Category.account == g.authorized_account)
            & (Category.direction == FundsDirection.EXPENSE.value)
        )
        .order_by(Category.name)
    )
    income_categories = (
        Category
        .select()
        .where(
            (Category.account == g.authorized_account)
            & (Category.direction == FundsDirection.INCOME.value)
        )
        .order_by(Category.name)
    )
    # fmt: on

    return render_template(
        "categories/view.html",
        expense_categories=expense_categories,
        income_categories=income_categories,
    )


@bp.route("/categories/new", methods=["POST"])
@auth.login_required
def new():
    redirect_url = url_for("categories.index")

    form = AddCategoryForm(request.form)
    utils.validate_form(form, redirect_url)

    direction = form.direction.data
    name = form.name.data
    color_sign = form.color_sign.data

    category = Category.create(
        account=g.authorized_account,
        direction=direction,
        name=name,
        color_sign=color_sign,
    )
    notify.info(f"New category {category.name} was created.")

    return redirect(redirect_url)


@bp.route("/categories/edit", methods=["POST"])
@auth.login_required
def edit():
    redirect_url = url_for("categories.index")

    form = EditCategoryForm(request.form)
    utils.validate_form(form, redirect_url)

    category_id = form.category_id.data
    name = form.name.data
    color_sign = form.color_sign.data

    category = Category.get_or_none(id=category_id, account=g.authorized_account)
    if category is None:
        notify.error("Category not found.")
        return redirect(redirect_url)

    if name is not None and name != category.name:
        category.name = name

    if color_sign is not None and color_sign != category.color_sign:
        category.color_sign = color_sign

    category.save()
    notify.info(f"Category {category.name} was updated.")

    return redirect(redirect_url)


@bp.route("/categories/delete", methods=["POST"])
@auth.login_required
def delete():
    redirect_url = url_for("categories.index")

    form = DeleteCategoryForm(request.form)
    utils.validate_form(form, redirect_url)

    category_id = form.category_id.data

    category = Category.get_or_none(id=category_id, account=g.authorized_account)
    if category is None:
        notify.error("Category not found.")
        return redirect(redirect_url)

    category.delete_instance()
    notify.info(f"Category {category.name} was deleted.")

    return redirect(redirect_url)
