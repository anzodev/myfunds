import logging

import flask
from flask import request as req


def _log_request():
    logger = logging.getLogger("myfunds.web")
    logger.info(f"{req.remote_addr} - {req.method} {req.full_path}")


def _errorhandler_404(e: Exception):
    logger = logging.getLogger("myfunds.web")
    error_msg = repr(e)
    status_code = e.code
    description = e.description
    return_url = flask.session.get("last_page")

    logger.error(error_msg)

    return flask.render_template(
        "pages/error.html",
        status_code=status_code,
        description=description,
        return_url=return_url,
    )


def init_app(app: flask.Flask) -> None:
    app.before_request(_log_request)
    app.errorhandler(404)(_errorhandler_404)
