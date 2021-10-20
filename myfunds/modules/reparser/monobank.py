import csv
from datetime import datetime
from typing import Iterable
from typing import Union

from .base import ProviderReport
from .base import Replenishment
from .base import Withdrawal


class MonobankBase(ProviderReport):
    currency_code: str = None
    currency_precision: int = None

    def parse(self) -> Iterable[Union[Replenishment, Withdrawal]]:
        with open(self.filename) as csvfile:
            reader = csv.reader(csvfile, delimiter=",")
            header = next(reader)
            if header != [
                "Дата i час операції",
                "Деталі операції",
                "MCC",
                f"Сума в валюті картки ({self.currency_code})",
                "Сума в валюті операції",
                "Валюта",
                "Курс",
                f"Сума комісій ({self.currency_code})",
                f"Сума кешбеку ({self.currency_code})",
                "Залишок після операції",
            ]:
                raise ValueError(f"Unexpected header ({header}).")

            for row in reader:
                amount = round(float(row[3]) * (10 ** self.currency_precision))
                created_at = datetime.strptime(row[0], "%d.%m.%Y %H:%M:%S")
                comment = row[1].replace("\n", " ")

                if amount > 0:
                    yield Replenishment(amount, created_at, comment)

                elif amount < 0:
                    yield Withdrawal(abs(amount), created_at, comment)
