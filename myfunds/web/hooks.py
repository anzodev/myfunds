import logging

from flask import Flask
from flask import Response
from flask import g
from flask import redirect
from flask import render_template
from flask import url_for
from werkzeug.exceptions import HTTPException
from werkzeug.exceptions import NotFound

from myfunds.web import auth
from myfunds.web import constants


def add_constants_to_globals():
    g.CONST_FUNDS_DIRECTION = constants.FundsDirection
    g.CONST_NO_CATEGORY_TXN_COLOR = constants.NO_CATEGORY_TXN_COLOR


def errorhandler(exc: Exception) -> Response:
    if isinstance(exc, auth.NotAuthorized):
        return redirect(url_for("access.login"))

    if isinstance(exc, auth.SessionCorrupted):
        auth.forget_account()
        return redirect(url_for("access.login"))

    if isinstance(exc, auth.NotSuperUser):
        exc = NotFound()

    status_code = 500
    description = (
        "Sorry, something goes wrong."
        " Try to repeat your request a few minutes later."
    )

    if isinstance(exc, HTTPException):
        status_code = exc.code
        description = exc.description

    if status_code == 500:
        logger = logging.getLogger(__name__)
        logger.exception("unexpected error:")

    return render_template(
        "pages/error.html", status_code=status_code, description=description
    )


def init_app(app: Flask) -> None:
    app.before_request(add_constants_to_globals)
    app.errorhandler(Exception)(errorhandler)
