import json
from datetime import datetime
from typing import Any
from typing import List
from typing import Optional

from myfunds.core.constants import FundsDirection


class TransactionJSONEncoder(json.JSONEncoder):
    def default(self, o: Any) -> Any:
        if isinstance(o, datetime):
            return o.strftime("%Y-%m-%d %H:%M:%S")
        return super().default(o)


class ProviderTransaction:
    direction: str = None

    def __init__(
        self,
        amount: int,
        created_at: datetime,
        comment: Optional[str] = None,
    ):
        self.amount = amount
        self.created_at = created_at
        self.comment = comment

    def to_dict(self) -> dict:
        return {
            "direction": self.direction,
            "amount": self.amount,
            "created_at": self.created_at,
            "comment": self.comment,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), cls=TransactionJSONEncoder)


class Replenishment(ProviderTransaction):
    direction = FundsDirection.INCOME


class Withdrawal(ProviderTransaction):
    direction = FundsDirection.EXPENSE


class BaseTxnFetcher:
    provider_id: str = None
    provider_name: str = None
    require_config: bool = True

    def __init__(self, config: Optional[dict] = None):
        self.config = config

    def fetch_transactions(self, since: datetime) -> List[ProviderTransaction]:
        if self.require_config and self.config is None:
            raise RuntimeError(
                f"{self.__class__.__name__} fetcher config not initialised."
            )

        if since > datetime.now():
            raise RuntimeError(
                "I can't fetch transactions from the future, invalid since value."
            )

        return self._fetch_transactions(since)

    def _fetch_transactions(self, since: datetime) -> List[ProviderTransaction]:
        raise NotImplementedError
