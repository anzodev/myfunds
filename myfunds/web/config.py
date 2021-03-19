from dataclasses import dataclass
from typing import Optional

from environs import Env


class DefaultVal:
    TEMPLATES_AUTO_RELOAD = True
    RUN_HOST = "localhost"
    RUN_PORT = 5000
    RUN_USE_RELOADER = True
    TIMEZONE = "UTC"
    LOGGING_DICT_CONFIG = "{}"


@dataclass
class Config:
    DB_NAME: str
    SECRET_KEY: str
    TEMPLATES_AUTO_RELOAD: bool
    RUN_HOST: str
    RUN_PORT: int
    RUN_USE_RELOADER: bool
    TIMEZONE: str
    LOGGING_DICT_CONFIG: str


def from_env(filepath: Optional[str] = None) -> Config:
    env = Env()
    env.read_env(path=filepath)

    with env.prefixed("MYFUNDS_WEB_"):
        # fmt: off
        return Config(
            DB_NAME=env.str("DB_NAME"),
            SECRET_KEY=env.str("SECRET_KEY"),
            TEMPLATES_AUTO_RELOAD=env.bool("TEMPLATES_AUTO_RELOAD", DefaultVal.TEMPLATES_AUTO_RELOAD),  # noqa: E501
            RUN_HOST=env.str("RUN_HOST", DefaultVal.RUN_HOST),
            RUN_PORT=env.int("RUN_PORT", DefaultVal.RUN_PORT),
            RUN_USE_RELOADER=env.bool("RUN_USE_RELOADER", DefaultVal.RUN_USE_RELOADER),  # noqa: E501
            TIMEZONE=env.str("TIMEZONE", DefaultVal.TIMEZONE),
            LOGGING_DICT_CONFIG=env.str("LOGGING_DICT_CONFIG", DefaultVal.LOGGING_DICT_CONFIG),  # noqa: E501
        )
        # fmt: on
