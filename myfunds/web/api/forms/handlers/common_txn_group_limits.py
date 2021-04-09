from flask import redirect
from flask import request
from flask import session
from flask import url_for

from myfunds.domain import models
from myfunds.web.tools import alerts
from myfunds.web.tools import auth


@auth.login_required
@auth.superuser_required
def add_common_txn_group_limit():
    name = request.form["name"]
    ccy_code_alpha = request.form["ccy_code_alpha"]
    month_limit = int(request.form["month_limit"])

    if month_limit <= 0:
        alerts.error("Некорректное значение лимита.")
        return redirect(
            session.get("last_page", url_for("page.common_txn_group_limits_new"))
        )

    currency = models.Currency.get_or_none(code_alpha=ccy_code_alpha)
    if currency is None:
        alerts.error(f"Валюта {ccy_code_alpha} не найдена.")
        return redirect(
            session.get("last_page", url_for("page.common_txn_group_limits_new"))
        )

    models.CommonTransactionGroupLimit.create(
        name=name,
        currency=currency,
        month_limit=month_limit,
    )
    alerts.success("Новый лимит успешно добавлен.")

    return redirect(url_for("page.common_txn_group_limits"))


@auth.login_required
@auth.superuser_required
def delete_common_txn_group_limit():
    limit_id = int(request.form["limit_id"])

    limit = models.CommonTransactionGroupLimit.get_or_none(id=limit_id)
    if limit is None:
        alerts.error(f"Лимит ({limit_id}) не найден.")
        return redirect(
            session.get("last_page", url_for("page.common_txn_group_limits"))
        )

    limit.delete_instance()
    alerts.info(f"Лимит ({limit_id}) удален.")

    return redirect(url_for("page.common_txn_group_limits"))


@auth.login_required
@auth.superuser_required
def add_common_limit_participant():
    limit_id = int(request.form["limit_id"])
    balance_id = int(request.form["balance"])
    txn_group_id = int(request.form["txn_group"])

    limit = models.CommonTransactionGroupLimit.get_or_none(id=limit_id)
    if limit is None:
        alerts.error(f"Лимит ({limit_id}) не найден.")
        return redirect(
            session.get("last_page", url_for("page.common_txn_group_limits"))
        )

    balance = models.Balance.get_or_none(id=balance_id)
    if balance is None:
        alerts.error(f"Баланс ({balance_id}) не найден.")
        return redirect(
            session.get(
                "last_page",
                url_for("page.common_txn_group_limit_participants", limit_id=limit_id),
            )
        )

    txn_group = models.TransactionGroup.get_or_none(id=txn_group_id)
    if txn_group is None:
        alerts.error(f"Группа ({txn_group_id}) не найдена.")
        return redirect(
            session.get(
                "last_page",
                url_for("page.common_txn_group_limit_participants", limit_id=limit_id),
            )
        )

    if balance.currency_id != limit.currency_id:
        alerts.error("Валюта баланса не соответствует лимиту.")
        return redirect(
            session.get(
                "last_page",
                url_for("page.common_txn_group_limit_participants", limit_id=limit_id),
            )
        )

    if balance.account_id != txn_group.account_id:
        alerts.error("Группа не доступна для выбранного баланса.")
        return redirect(
            session.get(
                "last_page",
                url_for("page.common_txn_group_limit_participants", limit_id=limit_id),
            )
        )

    models.CommonTransactionGroupLimitRelation.create(
        limit=limit,
        balance=balance,
        group=txn_group,
    )
    alerts.info("Участник успешно добавлен.")

    return redirect(
        session.get(
            "last_page",
            url_for("page.common_txn_group_limit_participants", limit_id=limit_id),
        )
    )
