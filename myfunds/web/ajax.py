import logging
from functools import wraps

from myfunds.web import auth


class Error(Exception):
    ...


def ajax_response(success: bool, payload: dict, error: str) -> dict:
    return {"success": success, "payload": payload, "error": error}


def success_response(payload: dict) -> dict:
    return ajax_response(True, payload, "")


def fail_response(error: str) -> dict:
    return ajax_response(False, None, error)


def ajax_endpoint(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        logger = logging.getLogger("myfunds.web.views")

        try:
            payload = f(*args, **kwargs)

        except Error as e:
            logger.warning(repr(e))
            return fail_response(str(e))

        except auth.AuthorizationError as e:
            logger.warning(repr(e))
            return fail_response("Authorization failed.")

        except Exception:
            logger.exception("unexpected error:")
            return fail_response("Authorization failed.")

        return success_response(payload)

    return wrapper
