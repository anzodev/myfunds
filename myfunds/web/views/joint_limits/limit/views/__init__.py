from functools import wraps

from flask import Blueprint
from flask import abort
from flask import g

from myfunds.core.models import JointLimit
from myfunds.web import utils


bp = Blueprint(
    "limit",
    __name__,
    url_prefix="/joint_limits/<int:limit_id>",
    template_folder="../templates",
)


def verify_limit(f):
    @wraps(f)
    def wrapper(limit_id: int, *args, **kwargs):
        limit = JointLimit.get_or_none(id=limit_id)
        if limit is None:
            abort(404)

        g.limit = limit
        g.currency = limit.currency
        g.amount_placeholder = utils.make_amount_placeholder(g.currency.precision)
        g.amount_pattern = utils.make_amount_pattern(g.currency.precision)

        return f(*args, **kwargs)

    return wrapper
