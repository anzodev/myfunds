import json
import logging
import threading
import time
from datetime import date as dt_date
from typing import List
from typing import Tuple


class InlineKeyboard:
    def __init__(self, rows: int):
        self._buttons = list([] for i in range(rows))

    def add_button(self, row: int, text: str, callback_data: str) -> None:
        self._buttons[row].append({"text": text, "callback_data": callback_data})

    def to_dict(self) -> dict:
        return {"inline_keyboard": self._buttons}

    def jsonify(self) -> str:
        return json.dumps(self.to_dict())


def get_logger() -> logging.Logger:
    return logging.getLogger("myfunds.tgbot")


def daemonize(f):
    def wrapper(*args, **kwargs):
        t = threading.Thread(target=f, args=args, kwargs=kwargs, daemon=True)
        t.start()

    return wrapper


def log_error_and_restart(delay: int = 0):
    def outer(f):
        def inner(*args, **kwargs):
            logger = get_logger()

            while True:
                try:
                    f(*args, **kwargs)
                except Exception:
                    logger.exception("Unexpected error:")

                logger.info(f"Run {f.__name__} after {delay}s delay...")
                time.sleep(delay)

        return inner

    return outer


def update_has_callback(update: dict) -> bool:
    return "callback_query" in update


def extract_chat_id(update: dict) -> str:
    message = (
        update["message"]
        if not update_has_callback(update)
        else update["callback_query"]["message"]
    )
    return message["chat"]["id"]


def extract_command(update: dict) -> str:
    return (
        update["message"]["text"]
        if not update_has_callback(update)
        else update["callback_query"]["data"]
    )


def extract_command_name(command: str) -> str:
    return command.split(" ")[0][1:]


def extract_command_args(command: str) -> Tuple[str]:
    parts = command.split(" ")
    if len(parts) == 1:
        return ()

    return tuple(parts[1:])


def calculate_available_years(max_years: int) -> List[int]:
    current_year = dt_date.today().year
    return [current_year] + [current_year - i for i in range(1, max_years + 1)]


def make_date_range_by_year_and_month(year: int, month: int) -> Tuple[dt_date, dt_date]:
    until_year = year if month < 12 else year + 1
    until_month = month + 1 if month < 12 else 1
    return (dt_date(year, month, 1), dt_date(until_year, until_month, 1))
