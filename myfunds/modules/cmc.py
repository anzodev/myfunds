import base64
from collections import namedtuple
from typing import Dict
from typing import List
from urllib.parse import urlparse

import requests
from lxml import html


CryptoCurrency = namedtuple("CryptoCurrency", ["id", "symbol", "name", "img"])


def extract_currency_id_from_img_src(img_src: str) -> int:
    # fmt: off
    return int(
        urlparse(img_src).path
        .split("/")[-1]
        .split(".")[0]
    )
    # fmt: on


def fetch_currency(url: str) -> CryptoCurrency:
    base_xpath = '//*[@id="__next"]/div/div/div[2]/div/div[1]/div[{}]/div/div[1]/div[1]'
    symbol_xpath = f"{base_xpath}/h2/small"
    name_xpath = f"{base_xpath}/h2"
    img_xpath = f"{base_xpath}/img"

    res = requests.get(url)
    tree = html.fromstring(res.content)

    block_number = None
    symbol = []

    expected_block_numbers = ["3", "2"]
    for i in expected_block_numbers:
        block_number = i
        symbol = tree.xpath(symbol_xpath.format(block_number))
        if len(symbol) != 0:
            break

    if len(symbol) == 0:
        raise ValueError("Unexpected HTML markup.")

    symbol = symbol[0].text
    name = tree.xpath(name_xpath.format(block_number))[0].text

    img = tree.xpath(img_xpath.format(block_number))
    img_src = img[0].attrib["src"]

    id_ = extract_currency_id_from_img_src(img_src)

    res = requests.get(img_src)
    img_body = base64.b64encode(res.content).decode()

    return CryptoCurrency(id_, symbol, name, img_body)


def fetch_prices(currencies_ids: List[int], convert: str = "USD") -> Dict[int, float]:
    url = "https://portal-api.coinmarketcap.com/v1/watchlist/ids"
    json_data = {"ids": currencies_ids, "convert": convert, "include_untracked": False}

    res = requests.post(url, json=json_data, timeout=4)
    data = res.json()

    result = {}
    for i in data["watchlist"]:
        result[i["id"]] = float(f"{i['quote'][convert]['price']:.2f}")

    return result
