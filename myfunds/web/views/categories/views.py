from flask import Blueprint
from flask import g
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for

from myfunds.core.models import Category
from myfunds.web import auth
from myfunds.web import notify
from myfunds.web.constants import FundsDirection
from myfunds.web.forms import AddCategoryForm
from myfunds.web.forms import DeleteCategoryForm
from myfunds.web.forms import EditCategoryForm


bp = Blueprint("categories", __name__, template_folder="templates")


@bp.route("/categories")
@auth.login_required
def index():
    exepnse_categories = (
        Category.select()
        .where(Category.direction == FundsDirection.EXPENSE.value)
        .order_by(Category.name)
    )
    income_categories = (
        Category.select()
        .where(Category.direction == FundsDirection.INCOME.value)
        .order_by(Category.name)
    )
    return render_template(
        "categories/view.html",
        exepnse_categories=exepnse_categories,
        income_categories=income_categories,
    )


@bp.route("/categories/new", methods=["POST"])
@auth.login_required
def new():
    form = AddCategoryForm(request.form)
    if not form.validate():
        notify.error("Form data validation error.")
        return redirect(url_for("categories.index"))

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

    return redirect(url_for("categories.index"))


@bp.route("/categories/edit", methods=["POST"])
@auth.login_required
def edit():
    form = EditCategoryForm(request.form)
    if not form.validate():
        notify.error("Form data validation error.")
        return redirect(url_for("categories.index"))

    category_id = form.category_id.data
    name = form.name.data
    color_sign = form.color_sign.data

    category = Category.get_or_none(id=category_id, account=g.authorized_account)
    if category is None:
        notify.error("Category not found.")
        return redirect(url_for("categories.index"))

    if name is not None and name != category.name:
        category.name = name

    if color_sign is not None and color_sign != category.color_sign:
        category.color_sign = color_sign

    category.save()
    notify.info(f"Category {category.name} was updated.")

    return redirect(url_for("categories.index"))


@bp.route("/categories/delete", methods=["POST"])
@auth.login_required
def delete():
    form = DeleteCategoryForm(request.form)
    if not form.validate():
        print(form.errors)
        notify.error("Form data validation error.")
        return redirect(url_for("categories.index"))

    category_id = form.category_id.data

    category = Category.get_or_none(id=category_id, account=g.authorized_account)
    if category is None:
        notify.error("Category not found.")
        return redirect(url_for("categories.index"))

    category.delete_instance()
    notify.info(f"Category {category.name} was deleted.")

    return redirect(url_for("categories.index"))
