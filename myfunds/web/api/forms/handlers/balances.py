import os
import tempfile
import uuid

from flask import current_app
from flask import g
from flask import redirect
from flask import request
from flask import session
from flask import url_for

from myfunds.domain import business
from myfunds.domain import models
from myfunds.domain.constants import TransactionType
from myfunds.tools import dates
from myfunds.tools import report_parser
from myfunds.web import constants as web_constants
from myfunds.web.tools import alerts
from myfunds.web.tools import auth


@auth.login_required
def add_balance():
    name = request.form["name"]
    ccy_code_alpha = request.form["ccy_code_alpha"]

    balance = models.Balance.get_or_none(name=name, account_id=g.account.id)
    if balance is not None:
        alerts.error("Баланс с таким именем уже существует.")
        return redirect(session.get("last_page", url_for("page.balances")))

    currency = models.Currency.get_or_none(code_alpha=ccy_code_alpha)
    if currency is None:
        alerts.error(f"Валюта {ccy_code_alpha} не найдена.")
        return redirect(session.get("last_page", url_for("page.balances")))

    business.create_balance(
        account=g.account,
        currency=currency,
        name=name,
    )
    alerts.success("Новый баланс успешно добавлен.")

    return redirect(url_for("page.balances"))


@auth.login_required
def update_balance():
    balance_id = request.form["balance_id"]
    name = request.form["name"]

    balance = models.Balance.get_or_none(id=balance_id, account=g.account)
    if balance is None:
        alerts.error(f"Баланс ({balance_id}) не найден.")
        return redirect(session.get("last_page", url_for("page.balances")))

    balance.name = name
    balance.save(only=[models.Balance.name])
    alerts.info(f"Баланс ({balance_id}) обновлен.")

    return redirect(url_for("page.balance_edit", balance_id=balance.id))


@auth.login_required
def delete_balance():
    balance_id = int(request.form["balance_id"])

    balance = models.Balance.get_or_none(id=balance_id, account=g.account)
    if balance is None:
        alerts.error(f"Баланс ({balance_id}) не найден.")
        return redirect(session.get("last_page", url_for("page.balances")))

    balance.delete_instance()
    alerts.info(f"Баланс ({balance_id}) удален.")

    return redirect(url_for("page.balances"))


@auth.login_required
def make_replenishment():
    tz = current_app.config["TIMEZONE"]
    dt_format = web_constants.DATETIME_FORMAT

    balance_id = int(request.form["balance_id"])
    amount = float(request.form["amount"])
    txn_group_id = request.form["txn_group_id"]
    created_at = request.form["created_at"]
    comment = request.form["comment"]

    url_params = {
        "amount": str(amount),
        "txn_group_id": txn_group_id,
        "comment": comment,
    }

    balance = models.Balance.get_or_none(id=balance_id, account=g.account)
    if balance is None:
        alerts.error(f"Баланс ({balance_id}) не найден.")
        return redirect(session.get("last_page", url_for("page.balances")))

    txn_group = None
    if txn_group_id != "NOTSET":
        txn_group = models.TransactionGroup.get_or_none(
            id=txn_group_id,
            account=g.account,
            type_=TransactionType.REPLENISHMENT,
        )
        if txn_group is None:
            alerts.error(f"Группа ({txn_group_id}) не найдена.")
            return redirect(
                url_for(
                    "page.balance_replenishment", balance_id=balance.id, **url_params
                )
            )

    utc_created_at = dates.make_utc_from_dt_str(created_at, dt_format, tz)

    business.make_replenishment(
        balance=balance,
        amount=int(amount * (10 ** balance.currency.base)),
        txn_group=txn_group,
        comment=comment,
        created_at=utc_created_at,
    )
    alerts.info(f"Баланс пополнен на сумму {amount} {balance.currency.code_alpha}.")

    return redirect(
        url_for("page.balance_replenishment", balance_id=balance.id, **url_params)
    )


@auth.login_required
def make_withdrawal():
    tz = current_app.config["TIMEZONE"]
    dt_format = web_constants.DATETIME_FORMAT

    balance_id = int(request.form["balance_id"])
    amount = float(request.form["amount"])
    txn_group_id = request.form["txn_group_id"]
    created_at = request.form["created_at"]
    comment = request.form["comment"]

    url_params = {
        "amount": str(amount),
        "txn_group_id": txn_group_id,
        "comment": comment,
    }

    balance = models.Balance.get_or_none(id=balance_id, account=g.account)
    if balance is None:
        alerts.error(f"Баланс ({balance_id}) не найден.")
        return redirect(session.get("last_page", url_for("page.balances")))

    txn_group = None
    if txn_group_id != "NOTSET":
        txn_group = models.TransactionGroup.get_or_none(
            id=txn_group_id,
            account=g.account,
            type_=TransactionType.WITHDRAWAL,
        )
        if txn_group is None:
            alerts.error(f"Группа ({txn_group_id}) не найдена.")
            return redirect(
                url_for("page.balance_withdrawal", balance_id=balance.id, **url_params)
            )

    utc_created_at = dates.make_utc_from_dt_str(created_at, dt_format, tz)

    business.make_withdrawal(
        balance=balance,
        amount=int(amount * (10 ** balance.currency.base)),
        txn_group=txn_group,
        comment=comment,
        created_at=utc_created_at,
    )
    alerts.info(f"С баланса выведено сумму {amount} {balance.currency.code_alpha}.")

    return redirect(
        url_for("page.balance_withdrawal", balance_id=balance.id, **url_params)
    )


@auth.login_required
def import_transactions():
    balance_id = int(request.form["balance_id"])
    source = request.form["source"]

    balance = models.Balance.get_or_none(id=balance_id, account=g.account)
    if balance is None:
        alerts.error(f"Баланс ({balance_id}) не найден.")
        return redirect(session.get("last_page", url_for("page.balances")))

    redirect_url = session.get(
        "last_page", url_for("page.balance_transactions", balance_id=balance.id)
    )

    if "report_file" not in request.files:
        alerts.error("Выберете файл отчета.")
        return redirect(redirect_url)

    report_file = request.files["report_file"]
    if report_file.filename == "":
        alerts.error("Файл отчета не выбран.")
        return redirect(redirect_url)

    with tempfile.TemporaryDirectory() as tmpdir:
        filename = uuid.uuid4().hex
        filepath = os.path.join(tmpdir, filename)
        report_file.save(filepath)

        report = None
        if source == "Privat24":
            report = report_parser.Privat24Report(filepath)

        if report is None:
            alerts.error("Неизвестный источник.")
            return redirect(redirect_url)

        for txn in report.get_transactions():
            func = None
            if txn.type_ == TransactionType.REPLENISHMENT:
                func = "make_replenishment"
            else:
                func = "make_withdrawal"

            getattr(business, func)(
                balance=balance,
                amount=txn.amount,
                comment=txn.comment,
                created_at=txn.created_at,
            )

    alerts.success("Транзакции успешно импортированы.")
    return redirect(redirect_url)


@auth.login_required
def update_transaction():
    balance_id = int(request.form["balance_id"])
    txn_id = int(request.form["txn_id"])
    txn_group_id = request.form.get("txn_group")
    comment = request.form.get("comment")

    balance = models.Balance.get_or_none(id=balance_id, account=g.account)
    if balance is None:
        alerts.error(f"Баланс ({balance_id}) не найден.")
        return redirect(session.get("last_page", url_for("page.balances")))

    txn = models.Transaction.get_or_none(id=txn_id, balance=balance)
    if txn is None:
        alerts.error(f"Транзакция ({txn_id}) не найдена.")
        return redirect(
            session.get(
                "last_page", url_for("page.balance_transactions", balance_id=balance.id)
            )
        )

    txn_group = None
    if txn_group_id is not None and txn_group_id != "NOTSET":
        txn_group = models.TransactionGroup.get_or_none(
            id=int(txn_group_id),
            account=g.account,
            type_=txn.type_,
        )
        if txn_group is None:
            alerts.error(f"Группа ({txn_group}) не найдена.")
            return redirect(
                session.get(
                    "last_page",
                    url_for("page.balance_transactions", balance_id=balance.id),
                )
            )

    txn.group = txn_group
    txn.comment = comment
    txn.save(only=[models.Transaction.group, models.Transaction.comment])
    alerts.info(f"Транзакция ({txn_id}) обновлена.")

    return redirect(
        session.get(
            "last_page",
            url_for("page.balance_transactions", balance_id=balance.id),
        )
    )


@auth.login_required
def delete_transaction():
    balance_id = int(request.form["balance_id"])
    txn_id = int(request.form["txn_id"])

    balance = models.Balance.get_or_none(id=balance_id, account=g.account)
    if balance is None:
        alerts.error(f"Баланс ({balance_id}) не найден.")
        return redirect(session.get("last_page", url_for("page.balances")))

    txn = models.Transaction.get_or_none(id=txn_id, balance=balance)
    if txn is None:
        alerts.error(f"Транзакция ({txn_id}) не найдена.")
        return redirect(
            session.get(
                "last_page", url_for("page.balance_transactions", balance_id=balance.id)
            )
        )

    business.rollback_transaction(txn)
    alerts.info(f"Транзакция ({txn_id}) удалена.")

    return redirect(
        session.get(
            "last_page",
            url_for("page.balance_transactions", balance_id=balance.id),
        )
    )
