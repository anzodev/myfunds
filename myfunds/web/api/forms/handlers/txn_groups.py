from flask import g
from flask import redirect
from flask import request
from flask import session
from flask import url_for

from myfunds.domain import business
from myfunds.domain import models
from myfunds.web.tools import alerts
from myfunds.web.tools import auth


@auth.login_required
def add_txn_group():
    type_ = request.form["txn_type"]
    name = request.form["name"]
    color_sign = request.form["color_sign"]

    business.create_txn_group(
        account=g.account,
        type_=type_,
        name=name,
        color_sign=color_sign,
    )
    alerts.success("Новая группа успешно добавлена.")

    return redirect(url_for("page.txn_groups"))


@auth.login_required
def update_txn_group():
    txn_group_id = int(request.form["txn_group_id"])
    name = request.form["name"]
    color_sign = request.form["color_sign"]

    txn_group = models.TransactionGroup.get_or_none(id=txn_group_id, account=g.account)
    if txn_group is None:
        alerts.error(f"Группа ({txn_group_id}) не найдена.")
        return redirect(session.get("last_page", url_for("page.txn_groups")))

    txn_group.name = name
    txn_group.color_sign = color_sign
    txn_group.save(
        only=[models.TransactionGroup.name, models.TransactionGroup.color_sign]
    )
    alerts.info(f"Группа ({txn_group.id}) обновлена.")

    return redirect(url_for("page.txn_group_edit", txn_group_id=txn_group.id))


@auth.login_required
def delete_txn_group():
    txn_group_id = int(request.form["txn_group_id"])

    txn_group = models.TransactionGroup.get_or_none(id=txn_group_id, account=g.account)
    if txn_group is None:
        alerts.error(f"Группа ({txn_group_id}) не найдена.")
        return redirect(session.get("last_page", url_for("page.txn_groups")))

    txn_group.delete_instance()
    alerts.info(f"Группа ({txn_group_id}) удалена.")

    return redirect(url_for("page.txn_groups"))
