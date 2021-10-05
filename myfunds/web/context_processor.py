from flask import Flask

from myfunds.web.utils import make_hrf_amount


def main_processor():
    return {"hrf_amount": make_hrf_amount}


def init_app(app: Flask) -> None:
    app.context_processor(main_processor)
