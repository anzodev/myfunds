import time
from dataclasses import dataclass

from myfunds.config import Config
from myfunds.core.models import Account
from myfunds.core.models import TelegramBotAccount
from myfunds.modules.tg import BotClient
from myfunds.modules.tg import BotClientError
from myfunds.tgbot import utils


@dataclass
class HandlerContext:
    client: BotClient
    config: Config
    account: Account
    chat_id: int
    command_args: tuple
    update: dict


class Bot:
    def __init__(self, config: Config):
        self._config = config
        self._client = BotClient(config.TGBOT_TOKEN)
        self._logger = utils.get_logger()

        self._handlers = {}

    def add_handler(self, command: str, handler) -> None:
        command_name = utils.extract_command_name(command)
        if command_name in self._handlers:
            raise RuntimeError(f"Command '{command}' is added already.")

        self._handlers[command_name] = handler

    @utils.log_error_and_restart(5)
    def run(self) -> None:
        self._logger.info("Starts listening for updates ...")

        offset = 0
        while True:
            try:
                updates = self._client.get_updates(
                    offset=offset,
                    limit=self._config.TGBOT_UPDATES_LIMIT,
                    timeout=self._config.TGBOT_UPDATES_TIMEOUT,
                )
            except BotClientError as e:
                self._logger.warning(repr(e))
                self._logger.info("Waiting for 10s ...")
                time.sleep(10)
                continue

            if len(updates) == 0:
                offset = 0
                continue

            for update in updates:
                self._process_update(update)

            offset = updates[-1]["update_id"] + 1

    @utils.daemonize
    def _process_update(self, update: dict) -> None:
        chat_id = utils.extract_chat_id(update)
        tg_account = TelegramBotAccount.get_or_none(chat_id=chat_id)
        if tg_account is None:
            self._client.send_message(
                chat_id=chat_id,
                text="\n".join(
                    [
                        f"Chat ID: {chat_id}",
                        "Sorry, this is a private bot, access denied.",
                    ]
                ),
            )
            return

        account = tg_account.account

        command = utils.extract_command(update)
        command_args = utils.extract_command_args(command)

        self._logger.info(f"{account.username}: {command}")

        handler = self._get_handler(command)
        if handler is None:
            self._logger.warning(f"Handler not found (command '{command}').")
            return

        ctx = HandlerContext(
            client=self._client,
            config=self._config,
            account=account,
            chat_id=chat_id,
            command_args=command_args,
            update=update,
        )

        try:
            return handler(ctx)
        except Exception:
            self._logger.exception("Unexpected error:")

    def _get_handler(self, command: str):
        command_name = utils.extract_command_name(command)
        if command_name:
            return self._handlers.get(command_name)

    def _is_chat_signed_up(self, chat_id: int) -> bool:
        return (
            TelegramBotAccount.select()
            .where(TelegramBotAccount.chat_id == chat_id)
            .exists()
        )
