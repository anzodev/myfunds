import re
from typing import Any
from typing import Callable
from typing import Iterable
from typing import List


def verify(value: Any, validators: List[Callable]) -> None:
    for v in validators:
        v(value)


def is_instance(instance: Any):
    def _is_instance(value: Any):
        if not isinstance(value, instance):
            raise ValueError(f"Value isn't the instance of {instance}.")

    return _is_instance


def eq(eq_value: Any):
    def _eq(value: Any):
        if value != eq_value:
            raise ValueError(f"Value isn't equal {repr(eq_value)}.")

    return _eq


def ne(ne_value: Any):
    def _ne(value: Any):
        if value == ne_value:
            raise ValueError(f"Value is equal {repr(ne_value)}.")

    return _ne


def lt(lt_value: Any):
    def _lt(value: Any):
        if value >= lt_value:
            raise ValueError(f"Value isn't less than {repr(lt_value)}.")

    return _lt


def le(le_value: Any):
    def _le(value: Any):
        if value > le_value:
            raise ValueError(f"Value isn't less than {repr(le_value)} or equal it.")

    return _le


def gt(gt_value: Any):
    def _gt(value: Any):
        if value <= gt_value:
            raise ValueError(f"Value isn't greater than {repr(gt_value)}.")

    return _gt


def ge(ge_value: Any):
    def _ge(value: Any):
        if value < ge_value:
            raise ValueError(f"Value isn't greater than {repr(ge_value)} or equal it.")

        return

    return _ge


def in_(in_value: Iterable):
    def _in_(value: Any):
        if value not in in_value:
            raise ValueError(f"Value isn't in {repr(in_value)}.")

    return _in_


def match(pattern: str):
    def _match(value: Any):
        if re.match(pattern, value) is None:
            raise ValueError("Value doesn't match.")

    return _match
