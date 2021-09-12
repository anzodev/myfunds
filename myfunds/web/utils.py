from argparse import ArgumentParser
from argparse import Namespace
from datetime import datetime


def env_parser() -> ArgumentParser:
    parser = ArgumentParser()
    parser.add_argument(
        "--env", type=str, default=None, help="environment configuration file path"
    )
    return parser


def parse_env_parser() -> Namespace:
    parser = env_parser()
    return parser.parse_args()


def make_amount_pattern(currency_precision: int) -> str:
    pattern = r"^[1-9]{1}\d*"
    if currency_precision == 0:
        return f"{pattern}$"

    fract_len = "{1}" if currency_precision == 1 else f"{{1,{currency_precision}}}"
    return f"{pattern}(\\.\\d{fract_len})?$"


def make_amount_placeholder(currency_precision: int) -> str:
    placeholder = "100"
    if currency_precision == 0:
        return placeholder
    return ".".join([placeholder, "0" * currency_precision])


def amount_to_subunits(amount_repr: str, currency_precision: int) -> int:
    return round(float(amount_repr) * (10 ** currency_precision))


def datetime_range_from_first_month_day_to_now() -> tuple[datetime, datetime]:
    now = datetime.now()
    return (now.replace(day=1, hour=0, minute=0, second=0, microsecond=0), now)
