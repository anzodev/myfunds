from datetime import datetime
from typing import List

from myfunds.modules.api.privat24 import MerchantAPI

from .base import BaseTxnFetcher
from .base import ProviderTransaction
from .base import Replenishment
from .base import Withdrawal


DATETIME_FORMAT = "%d.%m.%Y"


class Privat24TxnFetcher(BaseTxnFetcher):
    provider_id = "privat24"
    provider_name = "Privat24"
    require_config = True

    def _fetch_transactions(self, since: datetime) -> List[ProviderTransaction]:
        api = MerchantAPI(
            merchant_id=self.config["merchant_id"],
            merchant_password=self.config["merchant_password"],
            card=self.config["card"],
        )

        start_date = since.strftime(DATETIME_FORMAT)
        end_date = datetime.now().strftime(DATETIME_FORMAT)

        xml_data = api.payments(start_date, end_date)

        txns = []
        for i in xml_data.findall("./data/info/statements/statement"):
            created_at = datetime.strptime(
                f"{i.attrib['trandate']} {i.attrib['trantime']}",
                "%Y-%m-%d %H:%M:%S",
            )
            comment = i.attrib["description"]

            cardamount = i.attrib["cardamount"]
            ccy_precision = self.config["ccy_precision"]

            if cardamount.startswith("-"):
                amount = round(
                    float(cardamount[1:].split(" ")[0]) * 10 ** ccy_precision
                )
                txns.append(Withdrawal(amount, created_at, comment))
            else:
                amount = round(float(cardamount.split(" ")[0]) * 10 ** ccy_precision)
                txns.append(Replenishment(amount, created_at, comment))

        return txns
