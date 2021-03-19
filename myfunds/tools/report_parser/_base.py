import abc
import datetime
from typing import Iterable
from typing import Optional

from myfunds.domain.constants import TransactionType


class Transaction:
    type_ = None

    def __init__(
        self,
        amount: int,
        created_at: datetime.datetime,
        comment: Optional[str] = None,
    ):
        self.amount = amount
        self.created_at = created_at
        self.comment = comment

    def __repr__(self) -> str:
        return f"Transaction({self.amount}, {self.created_at}, {self.comment})"


class Replenishment(Transaction):
    type_ = TransactionType.REPLENISHMENT


class Withdrawal(Transaction):
    type_ = TransactionType.WITHDRAWAL


class ReportInterface(abc.ABC):
    @abc.abstractmethod
    def get_transactions(self) -> Iterable[Transaction]:
        ...
