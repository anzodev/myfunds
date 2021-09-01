from flask import Flask


def amount_repr(amount: int, currency_precision: int) -> str:
    return f"{amount / (10 ** currency_precision):.{currency_precision}f}"


def main_processor():
    return {"amount_repr": amount_repr}


def init_app(app: Flask) -> None:
    app.context_processor(main_processor)
