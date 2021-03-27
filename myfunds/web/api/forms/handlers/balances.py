import os
import tempfile
import uuid

import peewee as pw
from flask import Response
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

        if source == "Monobank":
            report = report_parser.MonobankReport(filepath, balance.currency.code_alpha)

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
def download_transactions():
    tz = current_app.config["TIMEZONE"]
    dt_format = web_constants.DATETIME_FORMAT

    balance_id = request.form["balance_id"]
    txn_type = request.form["txn_type"]
    txn_group_id = request.form["txn_group"]
    created_at_range = request.form["created_at_range"]

    balance = models.Balance.get_or_none(id=balance_id, account=g.account)
    if balance is None:
        alerts.error(f"Баланс ({balance_id}) не найден.")
        return redirect(session.get("last_page", url_for("page.balances")))

    since_dt_str, until_dt_str = created_at_range.split(" - ")
    since_dt = dates.make_utc_from_dt_str(since_dt_str, dt_format, tz)
    until_dt = dates.make_utc_from_dt_str(until_dt_str, dt_format, tz)

    query = (
        models.Transaction.select(
            models.Transaction.id,
            models.Transaction.type_,
            models.Transaction.amount,
            models.Transaction.balance_remainder,
            models.Transaction.comment,
            models.Transaction.created_at,
            models.Balance,
            models.TransactionGroup,
        )
        .join(models.Balance)
        .switch()
        .join(models.TransactionGroup, pw.JOIN.LEFT_OUTER)
        .where(
            (models.Transaction.balance == balance)
            & (models.Transaction.created_at.between(since_dt, until_dt))
        )
        .order_by(models.Transaction.created_at.desc())
    )

    if txn_type in TransactionType:
        query = query.where(models.Transaction.type_ == txn_type)

    if txn_group_id not in [None, ""] and txn_group_id == "NO_GROUP":
        query = query.where(models.Transaction.group.is_null())
    else:
        txn_group = models.TransactionGroup.get_or_none(
            id=txn_group_id, account=balance.account, type_=txn_type
        )
        if txn_group is not None:
            query = query.where(models.Transaction.group == txn_group)

    def generate_content():
        header = ["Время", "Тип", "Группа", "Сумма", "Валюта", "Комментарий"]
        yield ";".join(header)
        yield "\n"
        for i in query.iterator():
            yield ";".join(
                [
                    dates.make_local_from_utc(i.created_at, tz).strftime(dt_format),
                    i.type_,
                    i.group.name,
                    i.amount_repr(),
                    balance.currency.code_alpha,
                    i.comment,
                ]
            )
            yield "\n"

    filename = f"myfunds_{since_dt_str}_{until_dt_str}.csv"
    return Response(
        generate_content(),
        mimetype="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


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


@auth.login_required
def change_replenishment_group():
    balance_id = int(request.form["balance_id"])
    from_replenishment_group = request.form["from_replenishment_group"]
    to_replenishment_group = request.form["to_replenishment_group"]

    from_replenishment_group_id = (
        int(from_replenishment_group)
        if from_replenishment_group != "NO_GROUP"
        else None
    )

    if from_replenishment_group_id is not None:
        group = models.TransactionGroup.get_by_id(from_replenishment_group_id)
        if group.type_ != TransactionType.REPLENISHMENT:
            raise ValueError("Не верный тип группы.")

    to_replenishment_group_id = (
        int(to_replenishment_group) if to_replenishment_group != "NO_GROUP" else None
    )

    if to_replenishment_group_id is not None:
        group = models.TransactionGroup.get_by_id(to_replenishment_group_id)
        if group.type_ != TransactionType.REPLENISHMENT:
            raise ValueError("Не верный тип группы.")

    balance = models.Balance.get_or_none(id=balance_id, account=g.account)
    if balance is None:
        alerts.error(f"Баланс ({balance_id}) не найден.")
        return redirect(session.get("last_page", url_for("page.balances")))

    if from_replenishment_group_id == to_replenishment_group_id:
        alerts.error("Группы не могут быть идентичными.")
        return redirect(
            session.get(
                "last_page",
                url_for(
                    "page.balance_transaction_group_transfer", balance_id=balance.id
                ),
            )
        )

    where_condition = (
        (
            (models.Transaction.balance == balance)
            & (models.Transaction.type_ == TransactionType.REPLENISHMENT)
            & (models.Transaction.group_id == from_replenishment_group_id)
        )
        if from_replenishment_group_id is not None
        else (
            (models.Transaction.balance == balance)
            & (models.Transaction.type_ == TransactionType.REPLENISHMENT)
            & (models.Transaction.group.is_null())
        )
    )

    models.Transaction.update(group=to_replenishment_group_id).where(
        where_condition
    ).execute()
    alerts.info("Группа изменена.")

    return redirect(
        session.get(
            "last_page",
            url_for("page.balance_transaction_group_transfer", balance_id=balance.id),
        )
    )


@auth.login_required
def change_withdrawal_group():
    balance_id = int(request.form["balance_id"])
    from_withdrawal_group = request.form["from_withdrawal_group"]
    to_withdrawal_group = request.form["to_withdrawal_group"]

    from_withdrawal_group_id = (
        int(from_withdrawal_group) if from_withdrawal_group != "NO_GROUP" else None
    )

    if from_withdrawal_group_id is not None:
        group = models.TransactionGroup.get_by_id(from_withdrawal_group_id)
        if group.type_ != TransactionType.WITHDRAWAL:
            raise ValueError("Не верный тип группы.")

    to_withdrawal_group_id = (
        int(to_withdrawal_group) if to_withdrawal_group != "NO_GROUP" else None
    )

    if to_withdrawal_group_id is not None:
        group = models.TransactionGroup.get_by_id(to_withdrawal_group_id)
        if group.type_ != TransactionType.WITHDRAWAL:
            raise ValueError("Не верный тип группы.")

    balance = models.Balance.get_or_none(id=balance_id, account=g.account)
    if balance is None:
        alerts.error(f"Баланс ({balance_id}) не найден.")
        return redirect(session.get("last_page", url_for("page.balances")))

    if from_withdrawal_group_id == to_withdrawal_group_id:
        alerts.error("Группы не могут быть идентичными.")
        return redirect(
            session.get(
                "last_page",
                url_for(
                    "page.balance_transaction_group_transfer", balance_id=balance.id
                ),
            )
        )

    where_condition = (
        (
            (models.Transaction.balance == balance)
            & (models.Transaction.type_ == TransactionType.WITHDRAWAL)
            & (models.Transaction.group_id == from_withdrawal_group_id)
        )
        if from_withdrawal_group_id is not None
        else (
            (models.Transaction.balance == balance)
            & (models.Transaction.type_ == TransactionType.WITHDRAWAL)
            & (models.Transaction.group.is_null())
        )
    )

    models.Transaction.update(group=to_withdrawal_group_id).where(
        where_condition
    ).execute()
    alerts.info("Группа изменена.")

    return redirect(
        session.get(
            "last_page",
            url_for("page.balance_transaction_group_transfer", balance_id=balance.id),
        )
    )


@auth.login_required
def add_transaction_group_limit():
    balance_id = int(request.form["balance_id"])
    txn_group = int(request.form["txn_group"])
    month_limit = float(request.form["month_limit"])

    balance = models.Balance.get_or_none(id=balance_id, account=g.account)
    if balance is None:
        alerts.error(f"Баланс ({balance_id}) не найден.")
        return redirect(session.get("last_page", url_for("page.balances")))

    txn_group = models.TransactionGroup.get_or_none(
        id=txn_group,
        account=g.account,
        type_=TransactionType.WITHDRAWAL,
    )
    if txn_group is None:
        alerts.error(f"Группа ({txn_group}) не найдена.")
        return redirect(
            session.get(
                "last_page",
                url_for("page.balance_transaction_group_limits", balance_id=balance.id),
            )
        )

    limit = models.TransactionGroupLimit.create(
        balance=balance,
        group=txn_group,
        month_limit=int(month_limit * (10 ** balance.currency.base)),
    )
    alerts.info(f"Лимит ({limit.id}) добавлен.")

    return redirect(
        session.get(
            "last_page",
            url_for("page.balance_transaction_group_limits", balance_id=balance.id),
        )
    )


@auth.login_required
def update_transaction_group_limit():
    balance_id = int(request.form["balance_id"])
    limit_id = int(request.form["limit_id"])
    month_limit = float(request.form["month_limit"])

    balance = models.Balance.get_or_none(id=balance_id, account=g.account)
    if balance is None:
        alerts.error(f"Баланс ({balance_id}) не найден.")
        return redirect(session.get("last_page", url_for("page.balances")))

    limit = models.TransactionGroupLimit.get_or_none(id=limit_id, balance=balance)
    if limit is None:
        alerts.error(f"Лимит ({limit_id}) не найден.")
        return redirect(
            session.get(
                "last_page",
                url_for("page.balance_transaction_group_limits", balance_id=balance.id),
            )
        )

    limit.month_limit = int(month_limit * (10 ** balance.currency.base))
    limit.save()
    alerts.info(f"Лимит ({limit.id}) обновлен.")

    return redirect(
        session.get(
            "last_page",
            url_for("page.balance_transaction_group_limits", balance_id=balance.id),
        )
    )


@auth.login_required
def delete_transaction_group_limit():
    balance_id = int(request.form["balance_id"])
    limit_id = int(request.form["limit_id"])

    balance = models.Balance.get_or_none(id=balance_id, account=g.account)
    if balance is None:
        alerts.error(f"Баланс ({balance_id}) не найден.")
        return redirect(session.get("last_page", url_for("page.balances")))

    limit = models.TransactionGroupLimit.get_or_none(id=limit_id, balance=balance)
    if limit is None:
        alerts.error(f"Лимит ({limit_id}) не найден.")
        return redirect(
            session.get(
                "last_page",
                url_for("page.balance_transaction_group_limits", balance_id=balance.id),
            )
        )

    limit.delete_instance()
    alerts.info(f"Лимит ({limit_id}) удален.")

    return redirect(
        session.get(
            "last_page",
            url_for("page.balance_transaction_group_limits", balance_id=balance.id),
        )
    )
