from datetime import datetime
from typing import Iterable

import xlrd

from .base import ReportParser
from .base import Replenishment
from .base import Transaction
from .base import Withdrawal


class Privat24BaseParser(ReportParser):
    provider_name = "Privat24"
    header: list[str] = []
    sheet: str = None

    def parse(self) -> Iterable[Transaction]:
        wb = xlrd.open_workbook(self.filename)
        sheet = wb.sheet_by_name(self.sheet)
        rows = (sheet.row_values(i) for i in range(sheet.nrows))

        next(rows)
        header = next(rows)
        if header != self.header:
            raise ValueError(f"Unexpected header ({header}).")

        for row in rows:
            amount = round(row[5] * (10 ** self.currency_precision))
            comment = row[4]
            created_at = datetime.strptime(f"{row[0]} {row[1]}", "%d.%m.%Y %H:%M")

            if amount > 0:
                yield Replenishment(amount, created_at, comment)

            elif amount < 0:
                yield Withdrawal(abs(amount), created_at, comment)


class Privat24_UK_UAH(Privat24BaseParser):
    language = "UK"
    currency_code = "UAH"
    sheet = "Виписки"
    header = [
        "Дата",
        "Час",
        "Категорія",
        "Карта",
        "Опис операції",
        "Сума в валюті карти",
        "Валюта карти",
        "Сума в валюті транзакції",
        "Валюта транзакції",
        "Залишок на кінець періоду",
        "Валюта залишку",
    ]
