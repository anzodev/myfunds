import csv
from datetime import datetime
from typing import Iterable
from typing import List

from .base import Replenishment
from .base import ReportParser
from .base import Transaction
from .base import Withdrawal


class MonobankBaseParser(ReportParser):
    provider_name = "Monobank"
    header: List[str] = []

    def parse(self) -> Iterable[Transaction]:
        with open(self.filename) as csvfile:
            reader = csv.reader(csvfile, delimiter=",")
            header = next(reader)
            if header != self.header:
                raise ValueError(f"Unexpected header ({header}).")

            for row in reader:
                amount = round(float(row[3]) * (10 ** self.currency_precision))
                created_at = datetime.strptime(row[0], "%d.%m.%Y %H:%M:%S")
                comment = row[1].replace("\n", " ")

                if amount > 0:
                    yield Replenishment(amount, created_at, comment)

                elif amount < 0:
                    yield Withdrawal(abs(amount), created_at, comment)


class Monobank_UK_UAH(MonobankBaseParser):
    language = "UK"
    currency_code = "UAH"
    header = [
        "Дата i час операції",
        "Деталі операції",
        "MCC",
        "Сума в валюті картки (UAH)",
        "Сума в валюті операції",
        "Валюта",
        "Курс",
        "Сума комісій (UAH)",
        "Сума кешбеку (UAH)",
        "Залишок після операції",
    ]
