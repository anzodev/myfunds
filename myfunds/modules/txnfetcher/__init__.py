from typing import List
from typing import Optional
from typing import Type

from . import monobank
from . import privat24
from .base import BaseTxnFetcher


_fetchers = [
    monobank.MonobankTxnFetcher,
    privat24.Privat24TxnFetcher,
]
_fetchers_map = {i.provider_id: i for i in _fetchers}


def fetchers() -> List[Type[BaseTxnFetcher]]:
    return _fetchers.copy()


def get_fetcher(provider_id: str) -> Optional[Type[BaseTxnFetcher]]:
    return _fetchers_map.get(provider_id)
