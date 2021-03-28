import logging
from http import HTTPStatus
from traceback import format_exc

import flask
from werkzeug.exceptions import HTTPException

from myfunds.web.api.forms import handlers as hs
from myfunds.web.tools import auth


_bp = flask.Blueprint("form", __name__, url_prefix="/forms/")


@_bp.errorhandler(Exception)
def _errorhandler(e: Exception):
    logger = logging.getLogger("myfunds.web")
    error_msg = format_exc()

    if isinstance(e, (auth.NotAuthorizedError, auth.ForbiddenError)):
        logger.error(repr(e))
        auth.clear_session()
        return flask.redirect(flask.url_for("page.login"))

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


_method = "POST"
# fmt: off
_routes = [
    ("/login", "login", hs.authorization.login),
    ("/logout", "logout", hs.authorization.logout),

    ("/add-account", "add_account", hs.accounts.add_account),
    ("/update-password", "update_password", hs.accounts.update_password),
    ("/update-ip-whitelist", "update_ip_whitelist", hs.accounts.update_ip_whitelist),

    ("/add-currency", "add_currency", hs.currencies.add_currency),
    ("/update-currency", "update_currency", hs.currencies.update_currency),

    ("/add-balance", "add_balance", hs.balances.add_balance),
    ("/update-balance", "update_balance", hs.balances.update_balance),
    ("/delete-balance", "delete_balance", hs.balances.delete_balance),
    ("/make-replenishment", "make_replenishment", hs.balances.make_replenishment),
    ("/make-withdrawal", "make_withdrawal", hs.balances.make_withdrawal),
    ("/import-transactions", "import_transactions", hs.balances.import_transactions),
    ("/download-transactions", "download_transactions", hs.balances.download_transactions),  # noqa: E501
    ("/update-transaction", "update_transaction", hs.balances.update_transaction),
    ("/delete-transaction", "delete_transaction", hs.balances.delete_transaction),
    ("/add-transaction-group-limit", "add_transaction_group_limit", hs.balances.add_transaction_group_limit),  # noqa: E501
    ("/update-transaction-group-limit", "update_transaction_group_limit", hs.balances.update_transaction_group_limit),  # noqa: E501
    ("/delete-transaction-group-limit", "delete_transaction_group_limit", hs.balances.delete_transaction_group_limit),  # noqa: E501
    ("/change-replenishment-group", "change_replenishment_group", hs.balances.change_replenishment_group),  # noqa: E501
    ("/change-withdrawal-group", "change_withdrawal_group", hs.balances.change_withdrawal_group),  # noqa: E501

    ("/add-txn-group", "add_txn_group", hs.txn_groups.add_txn_group),
    ("/update-txn-group", "update_txn_group", hs.txn_groups.update_txn_group),
    ("/delete-txn-group", "delete_txn_group", hs.txn_groups.delete_txn_group),

    ("/add-crypto-balance", "add_crypto_balance", hs.crypto_balances.add_crypto_balance),  # noqa: E501
    ("/update-crypto-balance", "update_crypto_balance", hs.crypto_balances.update_crypto_balance),  # noqa: E501
    ("/delete-crypto-balance", "delete_crypto_balance", hs.crypto_balances.delete_crypto_balance),  # noqa: E501
]
# fmt: on
for rule, endpoint, handler in _routes:
    _bp.add_url_rule(rule, endpoint, handler, methods=[_method])


def init_app(app: flask.Flask) -> None:
    app.register_blueprint(_bp)
