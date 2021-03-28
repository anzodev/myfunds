from typing import Dict
from typing import List

import requests


def get_usd_price(symbols_ids: List[int]) -> Dict[int, float]:
    res = requests.post(
        "https://portal-api.coinmarketcap.com/v1/watchlist/ids",
        json={
            "ids": symbols_ids,
            "convert": "USD",
            "include_untracked": False,
        },
    )

    json_data = res.json()
    return {
        i["id"]: round(float(i["quote"]["USD"]["price"]), 2)
        for i in json_data["watchlist"]
    }
