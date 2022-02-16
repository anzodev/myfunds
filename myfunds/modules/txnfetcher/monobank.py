from datetime import datetime
from datetime import timedelta
from typing import List

from myfunds.modules.api.monobank import PersonalAPI

from .base import BaseTxnFetcher
from .base import ProviderTransaction
from .base import Replenishment
from .base import Withdrawal


class MonobankTxnFetcher(BaseTxnFetcher):
    provider_id = "monobank"
    provider_name = "Monobank"
    require_config = True

    def _fetch_transactions(self, since: datetime) -> List[ProviderTransaction]:
        api = PersonalAPI(self.config["token"])

        account = self.config["account"]
        from_ = int(since.timestamp())
        to = int((since + timedelta(days=30)).timestamp())

        data = api.payments(account, from_, to)

        txns = []
        for i in data:
            amount = i["amount"]
            created_at = datetime.fromtimestamp(float(i["time"]))
            comment = i["description"]

            if amount < 0:
                txns.append(Withdrawal(abs(amount), created_at, comment))

            elif amount > 0:
                txns.append(Replenishment(amount, created_at, comment))

        return txns
