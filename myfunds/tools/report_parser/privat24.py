import xlrd

from myfunds.tools import dates

from ._base import Replenishment
from ._base import ReportInterface
from ._base import Withdrawal


SHEET_NAME = "Виписки"
HEADING = [
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
DATETIME_FORMAT = "%d.%m.%Y %H:%M"
TIMEZONE = "Europe/Kiev"


class Report(ReportInterface):
    def __init__(self, filepath: str):
        self._filepath = filepath

    def get_transactions(self):
        wb = xlrd.open_workbook(self._filepath)
        sheet = wb.sheet_by_name(SHEET_NAME)
        rows = (sheet.row_values(i) for i in range(sheet.nrows))

        next(rows)
        heading = next(rows)
        if heading != HEADING:
            raise ValueError(f"Unexpected heading ({heading}).")

        for row in rows:
            amount = round(row[5] * 100)
            comment = row[4]

            dt_str = f"{row[0]} {row[1]}"
            created_at = dates.make_utc_from_dt_str(dt_str, DATETIME_FORMAT, TIMEZONE)

            if amount > 0:
                yield Replenishment(abs(amount), created_at, comment)
            else:
                yield Withdrawal(abs(amount), created_at, comment)
