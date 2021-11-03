from argparse import ArgumentParser
from dataclasses import dataclass
from typing import Optional

from environs import Env


@dataclass
class Config:
    SUPERUSER: str
    DATABASE_PATH: str
    PBKDF2_PWD_HASHER_HASH_FUNC: str
    PBKDF2_PWD_HASHER_ITERATIONS: int
    PBKDF2_PWD_HASHER_SALT_LENGTH: int
    MAX_YEARS_OF_STATISTICS: int
    LOGGING_CONFIG: dict

    WEB_SECRET_KEY: str
    WEB_RUN_ON_HOST: str
    WEB_RUN_ON_PORT: int


def init_config(env_path: Optional[str] = None) -> Config:
    env = Env()
    env.read_env(env_path)

    with env.prefixed("MYFUNDS_"):
        return Config(
            SUPERUSER=env.str("SUPERUSER"),
            DATABASE_PATH=env.str("DATABASE_PATH"),
            PBKDF2_PWD_HASHER_HASH_FUNC=env.str("PBKDF2_PWD_HASHER_HASH_FUNC"),
            PBKDF2_PWD_HASHER_ITERATIONS=env.int("PBKDF2_PWD_HASHER_ITERATIONS"),
            PBKDF2_PWD_HASHER_SALT_LENGTH=env.int("PBKDF2_PWD_HASHER_SALT_LENGTH"),
            MAX_YEARS_OF_STATISTICS=env.int("MAX_YEARS_OF_STATISTICS", 5),
            LOGGING_CONFIG=env.json("LOGGING_CONFIG", "{}"),
            WEB_SECRET_KEY=env.str("WEB_SECRET_KEY"),
            WEB_RUN_ON_HOST=env.str("WEB_RUN_ON_HOST", "localhost"),
            WEB_RUN_ON_PORT=env.int("WEB_RUN_ON_PORT", 8080),
        )


def init_env_parser() -> ArgumentParser:
    parser = ArgumentParser()
    parser.add_argument(
        "--env", type=str, default=None, help="environment configuration file path"
    )
    return parser
