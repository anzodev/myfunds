import logging
from datetime import datetime
from typing import Optional
from typing import Tuple

from wtforms import Form

from myfunds.web import notify
from myfunds.web.exceptions import FormValidationError


def make_amount_pattern(currency_precision: int) -> str:
    pattern = r"^\d+"
    if currency_precision == 0:
        return f"{pattern}$"

    fract_len = "{1}" if currency_precision == 1 else f"{{1,{currency_precision}}}"
    return f"{pattern}(\\.\\d{fract_len})?$"


def make_amount_placeholder(currency_precision: int) -> str:
    placeholder = "100"
    if currency_precision == 0:
        return placeholder
    return ".".join([placeholder, "0" * currency_precision])


def amount_to_subunits(hrf_amount: str, currency_precision: int) -> int:
    return round(float(hrf_amount) * (10 ** currency_precision))


def make_hrf_amount(amount: int, currency_precision: int) -> str:
    """Returns human readable format of the amount."""
    return f"{amount / (10 ** currency_precision):.{currency_precision}f}"


def datetime_range_from_first_month_day_to_now() -> Tuple[datetime, datetime]:
    now = datetime.now()
    return (now.replace(day=1, hour=0, minute=0, second=0, microsecond=0), now)


def current_year() -> int:
    return datetime.now().year


def current_month() -> int:
    return datetime.now().month


def disable_werkzeug_logs() -> None:
    logger = logging.getLogger("werkzeug")
    logger.disabled = True


def validate_form(
    form: Form,
    redirect_url: str,
    error_notify: Optional[str] = "Form data validation error.",
) -> None:
    if not form.validate():
        if error_notify is not None:
            notify.error(error_notify)
        raise FormValidationError(form, redirect_url)
