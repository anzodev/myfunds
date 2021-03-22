import logging

import flask
from flask import request as req


def _log_request():
    logger = logging.getLogger("myfunds.web")
    logger.info(f"{req.remote_addr} - {req.method} {req.full_path}")


def init_app(app: flask.Flask) -> None:
    app.before_request(_log_request)
