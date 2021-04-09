import logging
from http import HTTPStatus
from traceback import format_exc

import flask
from werkzeug.exceptions import HTTPException

from myfunds.web.api.pages import handlers as hs
from myfunds.web.tools import auth
from myfunds.web.tools import alerts


_bp = flask.Blueprint("page", __name__)


@_bp.after_request
def _after_request(res: flask.Response):
    flask.session["last_page"] = flask.request.full_path
    return res


@_bp.errorhandler(Exception)
def _errorhandler(e: Exception):
    logger = logging.getLogger("myfunds.web")
    error_msg = format_exc()

    if isinstance(e, (auth.NotAuthorizedError, auth.ForbiddenError)):
        logger.error(repr(e))
        auth.clear_session()
        return flask.redirect(flask.url_for(".login"))

    if isinstance(e, auth.NotSuperUserError):
        logger.error(repr(e))
        alerts.error("Доступ запрещен!")
        return flask.redirect(
            flask.session.get("last_page", flask.url_for("page.index"))
        )

    http_status = HTTPStatus.INTERNAL_SERVER_ERROR
    status_code, description = http_status.value, http_status.description
    if isinstance(e, HTTPException):
        error_msg = repr(e)
        status_code = e.code
        description = e.description

    logger.error(error_msg)

    return_url = flask.session.get("last_page")

    return flask.render_template(
        "pages/error.html",
        status_code=status_code,
        description=description,
        traceback=format_exc(),
        return_url=return_url,
    )


_method = "GET"
# fmt: off
_routes = [
    ("/login", "login", hs.entry.login),
    ("/new-account", "new_account", hs.entry.new_account),
    ("/", "index", hs.entry.index),

    ("/account/edit", "account_edit", hs.account.edit),

    ("/balances", "balances", hs.balances.main),
    ("/balances/new", "balances_new", hs.balances.new),
    ("/balances/<int:balance_id>/edit", "balance_edit", hs.balance.edit),
    ("/balances/<int:balance_id>/transactions", "balance_transactions", hs.balance.transactions),  # noqa: E501
    ("/balances/<int:balance_id>/replenishment", "balance_replenishment", hs.balance.replenishment),  # noqa:E501
    ("/balances/<int:balance_id>/withdrawal", "balance_withdrawal", hs.balance.withdrawal),  # noqa:E501
    ("/balances/<int:balance_id>/transaction-group-transfer", "balance_transaction_group_transfer", hs.balance.transaction_group_transfer),  # noqa:E501
    ("/balances/<int:balance_id>/transaction-group-limits", "balance_transaction_group_limits", hs.balance.transaction_group_limits),  # noqa:E501
    ("/balances/<int:balance_id>/statistic", "balance_statistic", hs.balance.statistic),  # noqa:E501

    ("/transaction-groups", "txn_groups", hs.txn_groups.main),
    ("/transaction-groups/new", "txn_groups_new", hs.txn_groups.new),
    ("/transaction-groups/<int:txn_group_id>/edit", "txn_group_edit", hs.txn_group.edit),  # noqa:E501

    ("/common-transaction-group-limits", "common_txn_group_limits", hs.common_txn_group_limits.main),  # noqa: E501
    ("/common-transaction-group-limits/new", "common_txn_group_limits_new", hs.common_txn_group_limits.new),  # noqa: E501
    ("/common-transaction-group-limits/<int:limit_id>/edit", "common_txn_group_limit_edit", hs.common_txn_group_limit.edit),  # noqa:E501
    ("/common-transaction-group-limits/<int:limit_id>/participants", "common_txn_group_limit_participants", hs.common_txn_group_limit.participants),  # noqa:E501

    ("/currencies", "currencies", hs.currencies.main),
    ("/currencies/new", "currencies_new", hs.currencies.new),
    ("/currencies/<int:currency_id>/edit", "currency_edit", hs.currency.edit),

    ("/crypto-balances", "crypto_balances", hs.crypto_balances.main),
    ("/crypto-balances/new", "crypto_balances_new", hs.crypto_balances.new),
    ("/crypto-balances/<int:crypto_balance_id>/edit", "crypto_balance_edit", hs.crypto_balance.edit),  # noqa: E501
]
# fmt: on

for rule, endpoint, handler in _routes:
    _bp.add_url_rule(rule, endpoint, handler, methods=[_method])


def init_app(app: flask.Flask) -> None:
    app.register_blueprint(_bp)
