from datetime import datetime
from typing import Iterable
from typing import Union

import xlrd

from .base import Provider
from .base import Replenishment
from .base import Withdrawal


class Privat24Provider(Provider):
    id = "privat24"
    name = "Privat24"

    def parse_report(
        self, filename: str, currency_precision: int = 2
    ) -> Iterable[Union[Replenishment, Withdrawal]]:
        wb = xlrd.open_workbook(filename)
        sheet = wb.sheet_by_name("Виписки")
        rows = (sheet.row_values(i) for i in range(sheet.nrows))

        next(rows)
        header = next(rows)
        if header != [
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
        ]:
            raise ValueError(f"Unexpected header ({header}).")

        for row in rows:
            amount = round(row[5] * (10 ** currency_precision))
            comment = row[4]
            created_at = datetime.strptime(f"{row[0]} {row[1]}", "%d.%m.%Y %H:%M")

            if amount > 0:
                yield Replenishment(amount, created_at, comment)

            elif amount < 0:
                yield Withdrawal(abs(amount), created_at, comment)
