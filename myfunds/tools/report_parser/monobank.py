import csv

from myfunds.tools import dates

from ._base import Replenishment
from ._base import ReportInterface
from ._base import Withdrawal


TIMEZONE = "Europe/Kiev"
DATETIME_FORMAT = "%d.%m.%Y %H:%M:%S"


class Report(ReportInterface):
    def __init__(self, filepath: str, ccy_code_alpha: str):
        self._filepath = filepath
        self._header = [
            "Дата i час операції",
            "Деталі операції",
            "MCC",
            f"Сума в валюті картки ({ccy_code_alpha})",
            "Сума в валюті операції",
            "Валюта",
            "Курс",
            f"Сума комісій ({ccy_code_alpha})",
            f"Сума кешбеку ({ccy_code_alpha})",
            "Залишок після операції",
        ]

    def get_transactions(self):
        with open(self._filepath) as csvfile:
            reader = csv.reader(csvfile, delimiter=",")
            header = next(reader)
            if header != self._header:
                raise ValueError(f"Unexpected header ({header}).")

            for row in reader:
                amount = round(float(row[3]) * 100)
                created_at = dates.make_utc_from_dt_str(
                    dt_str=row[0],
                    fmt=DATETIME_FORMAT,
                    tz=TIMEZONE,
                )
                comment = row[1].replace("\n", " ")

                if amount > 0:
                    yield Replenishment(amount, created_at, comment)

                if amount < 0:
                    yield Withdrawal(abs(amount), created_at, comment)
