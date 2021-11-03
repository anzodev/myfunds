from typing import Any
from typing import List
from typing import Optional
from typing import Union

import requests


class BotClientError(Exception):
    ...


class BotClient:
    url_root: str = "https://api.telegram.org"

    def __init__(self, token: str):
        self.token = token

    def get_me(self) -> dict:
        url = self._make_url("getMe")
        return self._request("GET", url)

    def get_updates(
        self,
        offset: Optional[int] = None,
        limit: Optional[int] = None,
        timeout: Optional[int] = None,
        allowed_updates: Optional[list] = None,
    ) -> dict:
        url = self._make_url("getUpdates")
        params = {}
        self._set_optional(params, "offset", offset)
        self._set_optional(params, "limit", limit)
        self._set_optional(params, "timeout", timeout)
        self._set_optional(params, "allowed_updates", allowed_updates)
        return self._request("GET", url, params=params)

    def send_message(
        self,
        chat_id: Union[str, int],
        text: str,
        parse_mode: Optional[str] = None,
        entities: List[dict] = None,
        disable_web_page_preview: Optional[bool] = None,
        disable_notification: Optional[bool] = None,
        reply_to_message_id: Optional[int] = None,
        allow_sending_without_reply: Optional[bool] = None,
        reply_markup: Optional[dict] = None,
    ) -> dict:
        url = self._make_url("sendMessage")
        params = {"chat_id": chat_id, "text": text}
        # fmt: off
        self._set_optional(params, "parse_mode", parse_mode)
        self._set_optional(params, "entities", entities)
        self._set_optional(params, "disable_web_page_preview", disable_web_page_preview)  # noqa: E501
        self._set_optional(params, "disable_notification", disable_notification)
        self._set_optional(params, "reply_to_message_id", reply_to_message_id)
        self._set_optional(params, "allow_sending_without_reply", allow_sending_without_reply)  # noqa: E501
        self._set_optional(params, "reply_markup", reply_markup)
        # fmt: on
        return self._request("GET", url, params=params)

    def edit_message_text(
        self,
        text: str,
        chat_id: Optional[Union[str, int]] = None,
        message_id: Optional[int] = None,
        inline_message_id: Optional[str] = None,
        parse_mode: Optional[str] = None,
        entities: Optional[List[dict]] = None,
        disable_web_page_preview: Optional[bool] = None,
        reply_markup: Optional[dict] = None,
    ) -> dict:
        url = self._make_url("editMessageText")
        params = {"text": text}
        # fmt: off
        self._set_optional(params, "chat_id", chat_id)
        self._set_optional(params, "message_id", message_id)
        self._set_optional(params, "inline_message_id", inline_message_id)
        self._set_optional(params, "parse_mode", parse_mode)
        self._set_optional(params, "entities", entities)
        self._set_optional(params, "disable_web_page_preview", disable_web_page_preview)  # noqa: E501
        self._set_optional(params, "reply_markup", reply_markup)
        # fmt: on
        return self._request("GET", url, params=params)

    def edit_message_reply_markup(
        self,
        chat_id: Optional[Union[str, int]] = None,
        message_id: Optional[int] = None,
        inline_message_id: Optional[str] = None,
        reply_markup: Optional[dict] = None,
    ) -> dict:
        url = self._make_url("editMessageReplyMarkup")
        params = {}
        # fmt: off
        self._set_optional(params, "chat_id", chat_id)
        self._set_optional(params, "message_id", message_id)
        self._set_optional(params, "inline_message_id", inline_message_id)
        self._set_optional(params, "reply_markup", reply_markup)
        # fmt: on
        return self._request("GET", url, params=params)

    def delete_message(self, chat_id: Union[str, int], message_id: int) -> dict:
        url = self._make_url("deleteMessage")
        params = {"chat_id": chat_id, "message_id": message_id}
        return self._request("GET", url, params=params)

    def _make_url(self, method: str) -> str:
        return f"{self.url_root}/bot{self.token}/{method}"

    def _request(self, *args, **kwargs) -> dict:
        try:
            res = requests.request(*args, **kwargs)
        except requests.RequestException as e:
            raise BotClientError(f"Network error - {repr(e)}.")

        self._check_response(res)
        return res.json()["result"]

    def _check_response(self, res: requests.Response) -> None:
        try:
            json_data = res.json()
        except ValueError:
            raise BotClientError("No JSON.")

        ok = json_data.get("ok")
        if ok is None:
            raise BotClientError("Unknown result status.")

        if not ok:
            raise BotClientError(f"Failed request ({json_data.get('description')}).")

        result = json_data.get("result")
        if result is None:
            raise BotClientError("No result.")

    def _set_optional(self, params: dict, key: str, value: Any) -> None:
        if value is not None:
            params[key] = value
