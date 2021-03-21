from collections import namedtuple
from functools import wraps

from flask import abort
from flask import current_app
from flask import g
from flask import request
from flask import session

from ...domain import models


AccountInfo = namedtuple("AccountInfo", ["id", "username"])


class NotAuthorizedError(Exception):
    pass


class ForbiddenError(Exception):
    pass


def authorize_account(account: models.Account) -> None:
    session["aid"] = account.id


def is_authorized() -> bool:
    return "aid" in session


def clear_session() -> None:
    session.pop("aid", None)


def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        account_id = session.get("aid")
        if account_id is None:
            raise NotAuthorizedError()

        account = models.Account.get_or_none(id=account_id)
        if account is None:
            raise NotAuthorizedError()

        if (
            len(account.ip_whitelist) != 0
            and request.remote_addr not in account.ip_whitelist
        ):
            raise ForbiddenError()

        g.account = account
        g.is_superuser = g.account.username == current_app.config["SUPERUSER"]

        return f(*args, **kwargs)

    return wrapper
