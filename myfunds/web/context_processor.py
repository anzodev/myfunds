from typing import Optional

from flask import Flask
from flask import g

from myfunds.web.utils import make_hrf_amount


def hrf_amount(amount: int, currency_precision: Optional[int] = None) -> str:
    currency_precision = (
        currency_precision if currency_precision is not None else g.currency.precision
    )
    return make_hrf_amount(amount, currency_precision)


def main_processor():
    return {"hrf_amount": hrf_amount}


def init_app(app: Flask) -> None:
    app.context_processor(main_processor)
