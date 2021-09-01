import re
from typing import Any
from typing import Callable
from typing import Iterable
from typing import List
from typing import Type


class ValidationError(Exception):
    ...


def is_instance(cls: Type):
    def _is_instance(value: Any):
        if not isinstance(value, cls):
            raise ValidationError(f"Value isn't the instance of {repr(cls)}.")

    return _is_instance


def eq(eq_value: Any):
    def _eq(value: Any):
        if value != eq_value:
            raise ValidationError(f"Value isn't equal {repr(eq_value)}.")

    return _eq


def ne(ne_value: Any):
    def _ne(value: Any):
        if value == ne_value:
            raise ValidationError(f"Value is equal {repr(ne_value)}.")

    return _ne


def lt(lt_value: Any):
    def _lt(value: Any):
        if value >= lt_value:
            raise ValidationError(f"Value have to be less than {repr(lt_value)}.")

    return _lt


def le(le_value: Any):
    def _le(value: Any):
        if value > le_value:
            raise ValidationError(
                f"Value have to be less than {repr(le_value)} or equal it."
            )

    return _le


def gt(gt_value: Any):
    def _gt(value: Any):
        if value <= gt_value:
            raise ValidationError(f"Value have to be greater than {repr(gt_value)}.")

    return _gt


def ge(ge_value: Any):
    def _ge(value: Any):
        if value < ge_value:
            raise ValidationError(
                f"Value have to be greater than {repr(ge_value)} or equal it."
            )

        return

    return _ge


def one_of(values: Iterable):
    def _one_of(value: Any):
        if value not in values:
            raise ValidationError(f"Value isn't one of the {repr(values)}.")

    return _one_of


def match(pattern: str):
    def _match(value: Any):
        if re.match(pattern, value) is None:
            raise ValidationError("Value doesn't match the pattern.")

    return _match


def value(value: Any, validators: List[Callable]) -> None:
    for v in validators:
        v(value)
