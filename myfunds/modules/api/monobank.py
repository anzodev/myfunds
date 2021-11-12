from typing import List
from typing import Optional
from typing import Union
from urllib.parse import urljoin

import requests


class PersonalAPI:
    url_root = "https://api.monobank.ua"

    def __init__(self, token: str):
        self._token = token

    def client_info(self) -> dict:
        url = urljoin(self.url_root, "/personal/client-info")
        return self._make_request("GET", url)

    def payments(
        self, account: str, from_: int, to_: Optional[int] = None
    ) -> List[dict]:
        path = f"/personal/statement/{account}/{from_}"
        if to_ is not None:
            path = f"{path}/{to_}"

        url = urljoin(self.url_root, path)
        return self._make_request("GET", url)

    def _make_request(self, *args, **kwargs) -> Union[dict, list]:
        headers = kwargs.pop("headers", {})
        headers["X-Token"] = self._token
        res = requests.request(*args, headers=headers, **kwargs)
        return res.json()
