import requests


def fetch_exchange_rates() -> dict:
    # fmt: off
    return (
        requests.get("http://www.convertmymoney.com/rates.json", timeout=3)
        .json()
        .get("rates", {})
    )
    # fmt: on
