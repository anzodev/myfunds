from typing import Any
from typing import Dict
from typing import List
from typing import Union

from myfunds.core import constants


class Constant:
    def __init__(self, value: Union[int, str], **meta: Any):
        self._value = value
        self.meta = meta

    def __repr__(self) -> str:
        return f"Constant({repr(self.value)})"

    @property
    def value(self):
        return self._value


class ConstantGroup:
    @classmethod
    def constants(cls) -> List[Constant]:
        return list(i for i in vars(cls).values() if isinstance(i, Constant))

    @classmethod
    def values(cls) -> List[Union[int, str]]:
        return list(sorted(i.value for i in cls.constants()))

    @classmethod
    def to_dict(cls) -> Dict[Union[str, int], Constant]:
        return {i.value: i for i in cls.constants()}

    @classmethod
    def get(cls, value: Union[str, int]) -> Constant:
        return cls.to_dict()[value]


class FundsDirection(ConstantGroup):
    EXPENSE = Constant(constants.FundsDirection.EXPENSE, name="Expense")
    INCOME = Constant(constants.FundsDirection.INCOME, name="Income")


DATETIME_FORMAT = Constant("%Y-%m-%d %H:%M:%S")
DATETIME_PATTERN = Constant(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}")
NO_CATEGORY_TXN_COLOR = "#bcbcbc"
NO_CATEGORY_ID = -1
