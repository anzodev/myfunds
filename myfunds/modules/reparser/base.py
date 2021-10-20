import abc
import datetime
from typing import Iterable
from typing import Optional


class _Transaction:
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
        return (
            f"{self.__class__.__name__}({self.amount}, {self.created_at}, "
            f"{self.comment})"
        )


class Replenishment(_Transaction):
    ...


class Withdrawal(_Transaction):
    ...


class ProviderReport(abc.ABC):
    def __init__(self, filename: str):
        self.filename = filename

    @abc.abstractmethod
    def parse(self) -> Iterable[_Transaction]:
        ...
