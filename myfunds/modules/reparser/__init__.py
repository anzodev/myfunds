from .base import Provider
from .base import Replenishment
from .base import Withdrawal
from .base import _Transaction
from .monobank import MonobankProvider
from .privat24 import Privat24Provider


_providers = [MonobankProvider, Privat24Provider]
_providers_map = {i.id: i for i in _providers}


def get_provider(id_: str) -> Provider:
    return _providers_map.get(id_)


def get_providers() -> list[Provider]:
    return sorted(_providers.copy(), key=lambda i: i.name)


def is_replenishment(txn: _Transaction) -> bool:
    return isinstance(txn, Replenishment)


def is_withdrawal(txn: _Transaction) -> bool:
    return isinstance(txn, Withdrawal)
