import datetime

import flask

from myfunds.tools import dates
from myfunds.web import constants


def _utc_dt_to_local_dt(dt: datetime.datetime) -> str:
    tz = flask.current_app.config["TIMEZONE"]
    local_dt = dates.make_local_from_utc(dt, tz)
    return local_dt.strftime(constants.DATETIME_FORMAT)


def _utc_dt_to_local_d(dt: datetime.datetime) -> str:
    tz = flask.current_app.config["TIMEZONE"]
    local_dt = dates.make_local_from_utc(dt, tz)
    return local_dt.strftime(constants.DATE_FORMAT)


def init_app(app: flask.Flask) -> None:
    app.template_filter("utc_dt_to_local_dt")(_utc_dt_to_local_dt)
    app.template_filter("utc_dt_to_local_d")(_utc_dt_to_local_d)
