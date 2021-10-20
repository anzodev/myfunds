import logging

from flask import Flask
from flask import Response
from flask import g
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
from werkzeug.exceptions import HTTPException
from werkzeug.exceptions import NotFound

from myfunds.web import auth
from myfunds.web import constants
from myfunds.web.exceptions import FormValidationError


def add_constants_to_globals():
    g.CONST_FUNDS_DIRECTION = constants.FundsDirection
    g.CONST_NO_CATEGORY_TXN_COLOR = constants.NO_CATEGORY_TXN_COLOR


def setup_logger():
    g.logger = logging.getLogger(f"web.views.{request.endpoint}")


def errorhandler(exc: Exception) -> Response:
    if isinstance(exc, auth.NotAuthorized):
        return redirect(url_for("access.login"))

    if isinstance(exc, auth.SessionCorrupted):
        auth.forget_account()
        return redirect(url_for("access.login"))

    if isinstance(exc, auth.NotSuperUser):
        exc = NotFound()

    if isinstance(exc, FormValidationError):
        g.logger.warning(repr(exc))
        return redirect(exc.redirect_url)

    status_code = 500
    description = (
        "Sorry, something goes wrong."
        " Try to repeat your request a few minutes later."
    )

    if isinstance(exc, HTTPException):
        status_code = exc.code
        description = exc.description

    if status_code == 500:
        g.logger.exception("unexpected error:")

    return render_template(
        "pages/error.html", status_code=status_code, description=description
    )


def log_request():
    r = request
    if r.endpoint == "static":
        return

    logger = logging.getLogger("web.requests")

    query_string = r.query_string.decode()
    url = f"{r.path}?{query_string}" if query_string != "" else r.path
    logger.info(f"{r.remote_addr} {r.method} {url}")


def init_app(app: Flask) -> None:
    app.before_request(add_constants_to_globals)
    app.before_request(setup_logger)
    app.before_request(log_request)
    app.errorhandler(Exception)(errorhandler)
