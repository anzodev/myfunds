import datetime
from typing import Tuple

import pytz


def make_utc_from_dt(dt: datetime.datetime, tz: str) -> datetime.datetime:
    localized_dt = pytz.timezone(tz).localize(dt)
    return localized_dt.astimezone(pytz.UTC).replace(tzinfo=None)


def make_utc_from_dt_str(dt_str: str, fmt: str, tz: str) -> datetime.datetime:
    return make_utc_from_dt(datetime.datetime.strptime(dt_str, fmt), tz)


def make_utc_range_since_first_month_day_to_now() -> Tuple[
    datetime.datetime, datetime.datetime
]:
    utc_now = datetime.datetime.utcnow()
    return (
        utc_now.replace(day=1, hour=0, minute=0, second=0, microsecond=0),
        utc_now,
    )


def make_local_from_utc(dt: datetime.datetime, local_tz: str) -> datetime.datetime:
    utc_dt = pytz.UTC.localize(dt)
    return utc_dt.astimezone(pytz.timezone(local_tz)).replace(tzinfo=None)


def make_local_range_since_first_month_day_to_now(
    local_tz: str,
) -> Tuple[datetime.datetime, datetime.datetime]:
    utc_now = datetime.datetime.utcnow()
    local_now = make_local_from_utc(utc_now, local_tz=local_tz)
    return (
        local_now.replace(day=1, hour=0, minute=0, second=0, microsecond=0),
        local_now,
    )
