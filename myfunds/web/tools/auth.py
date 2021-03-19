from collections import namedtuple
from functools import wraps

from flask import g
from flask import session

from ...domain import models


AccountInfo = namedtuple("AccountInfo", ["id", "username"])


class NotAuthorizedError(Exception):
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

        g.account = models.Account.get_or_none(id=account_id)
        if g.account is None:
            raise NotAuthorizedError()

        return f(*args, **kwargs)

    return wrapper
