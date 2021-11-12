from hashlib import md5
from hashlib import sha1
from urllib.parse import urljoin
from xml.etree import ElementTree as ET

import requests
from defusedxml import ElementTree as DefusedET


class MerchantAPI:
    url_root = "https://api.privatbank.ua/p24api/"

    def __init__(self, merchant_id: str, merchant_password: str, card: str):
        self._merchant_id = merchant_id
        self._merchant_password = merchant_password
        self._card = card

    def card_info(self) -> DefusedET:
        url = urljoin(self.url_root, "balance")

        el_data = ET.Element("data")
        ET.SubElement(el_data, "oper").text = "cmt"
        ET.SubElement(el_data, "wait").text = "0"
        ET.SubElement(el_data, "test").text = "0"
        el_payment = ET.SubElement(el_data, "payment", attrib={"id": ""})
        ET.SubElement(
            el_payment, "prop", attrib={"name": "cardnum", "value": self._card}
        )
        ET.SubElement(el_payment, "prop", attrib={"name": "country", "value": "UA"})

        return self._make_request_data_and_send(url, el_data)

    def payments(self, start_date: str, end_date: str) -> DefusedET:
        url = urljoin(self.url_root, "rest_fiz")

        el_data = ET.Element("data")
        ET.SubElement(el_data, "oper").text = "cmt"
        ET.SubElement(el_data, "wait").text = "0"
        ET.SubElement(el_data, "test").text = "0"
        payment = ET.SubElement(el_data, "payment", attrib={"id": ""})
        ET.SubElement(payment, "prop", attrib={"name": "sd", "value": start_date})
        ET.SubElement(payment, "prop", attrib={"name": "ed", "value": end_date})
        ET.SubElement(payment, "prop", attrib={"name": "card", "value": self._card})

        return self._make_request_data_and_send(url, el_data)

    def _make_request_data_and_send(self, url: str, el_data: ET.Element) -> DefusedET:
        el_request = ET.Element("request")
        el_merchant = ET.SubElement(el_request, "merchant")
        ET.SubElement(el_merchant, "id").text = self._merchant_id
        ET.SubElement(el_merchant, "signature").text = self._make_signature(el_data)
        el_request.append(el_data)

        res = requests.post(
            url=url,
            headers={"Content-Type": "application/xml"},
            data=(
                '<?xml version="1.0" encoding="UTF-8"?>\n'
                f'{ET.tostring(el_request, encoding="UTF-8").decode()}'
            ),
        )

        return DefusedET.fromstring(res.text)

    def _make_signature(self, el_data: ET.Element) -> str:
        # Convert data element to the string and trim 'data' tags.
        data = ET.tostring(el_data).decode()[6:-7]
        payload = f"{data}{self._merchant_password}".encode()
        return sha1(md5(payload).hexdigest().encode()).hexdigest()
