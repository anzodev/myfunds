import datetime
import hashlib
from typing import Iterable
from typing import Optional


class Transaction:
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


class Replenishment(Transaction):
    ...


class Withdrawal(Transaction):
    ...


class ReportParser:
    provider_name: str = None
    language: str = None
    currency_code: str = None
    currency_precision: int = 2

    def __init__(self, filename: str):
        self.filename = filename

    def parse(self) -> Iterable[Transaction]:
        raise NotImplementedError

    @classmethod
    def name(cls, include_language: bool = True, include_currency: bool = True) -> str:
        parts = [cls.provider_name]
        if include_language:
            parts.append(cls.language.upper())
        if include_currency:
            parts.append(cls.currency_code.upper())
        return " - ".join(parts)

    @classmethod
    def identifier(cls) -> str:
        return hashlib.sha1(
            f"{cls.provider_name}{cls.language}{cls.currency_code}".encode()
        ).hexdigest()
