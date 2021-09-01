from functools import wraps

from flask import current_app
from flask import g
from flask import session

from myfunds.core.models import Account


class AuthorizationError(Exception):
    ...


class NotAuthorized(AuthorizationError):
    ...


class SessionCorrupted(AuthorizationError):
    ...


class NotSuperUser(AuthorizationError):
    ...


def authorize_account(account: Account) -> None:
    session["aid"] = account.id


def forget_account() -> None:
    session.pop("aid", None)


def session_has_account_id() -> bool:
    return "aid" in session


def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        account_id = session.get("aid")
        if account_id is None:
            raise NotAuthorized()

        account = Account.get_or_none(id=account_id)
        if account is None:
            raise SessionCorrupted()

        g.authorized_account = account
        g.is_superuser = account.username == current_app.config["SUPERUSER"]

        return f(*args, **kwargs)

    return wrapper


def superuser_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not hasattr(g, "authorized_account"):
            raise RuntimeError("You must first authorize an account.")

        if not g.is_superuser:
            raise NotSuperUser()

        return f(*args, **kwargs)

    return wrapper
