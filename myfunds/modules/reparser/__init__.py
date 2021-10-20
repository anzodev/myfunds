from typing import Type

from . import monobank
from . import privat24
from .base import Replenishment
from .base import ReportParser
from .base import Transaction
from .base import Withdrawal


_report_parsers = [
    monobank.Monobank_UK_UAH,
    privat24.Privat24_UK_UAH,
]
_report_parsers_map = {i.identifier(): i for i in _report_parsers}


def get_parser(id_: str) -> Type[ReportParser]:
    return _report_parsers_map.get(id_)


def get_parsers() -> list[Type[ReportParser]]:
    return list(sorted(_report_parsers.copy(), key=lambda i: i.name()))


def get_parsers_by_currency(currency_code: str) -> list[Type[ReportParser]]:
    return list(filter(lambda i: i.currency_code == currency_code, get_parsers()))


def is_replenishment(txn: Transaction) -> bool:
    return isinstance(txn, Replenishment)


def is_withdrawal(txn: Transaction) -> bool:
    return isinstance(txn, Withdrawal)
