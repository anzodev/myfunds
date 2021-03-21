from flask import redirect
from flask import request
from flask import session
from flask import url_for

from myfunds.domain import business
from myfunds.domain import models
from myfunds.web.tools import alerts
from myfunds.web.tools import auth


@auth.login_required
def add_currency():
    code_alpha = request.form["code_alpha"].upper()
    code_num = request.form["code_num"]
    base = int(request.form["base"])

    business.create_currency(
        code_alpha=code_alpha,
        code_num=code_num,
        base=int(base),
    )
    alerts.success("Новая валюта успешно добавлена.")

    return redirect(url_for("page.currencies"))


@auth.login_required
def update_currency():
    currency_id = int(request.form["currency_id"])
    code_alpha = request.form["code_alpha"].upper()
    code_num = int(request.form["code_num"])
    base = int(request.form["base"])

    currency = models.Currency.get_or_none(id=currency_id)
    if currency is None:
        alerts.error(f"Валюта ({currency_id}) не найдена.")
        return redirect(session.get("last_page", url_for("page.currencies")))

    currency.code_alpha = code_alpha
    currency.code_num = code_num
    currency.base = base
    currency.save(
        only=[
            models.Currency.code_alpha,
            models.Currency.code_num,
            models.Currency.base,
        ]
    )
    alerts.info(f"Валюта ({currency.id}) обновлена.")

    return redirect(url_for("page.currency_edit", currency_id=currency.id))
