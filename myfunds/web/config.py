from dataclasses import dataclass
from typing import Optional

from environs import Env


@dataclass
class Config:
    SUPERUSER: str
    SECRET_KEY: str
    DATABASE_PATH: str
    PBKDF2_PWD_HASHER_HASH_FUNC: str
    PBKDF2_PWD_HASHER_ITERATIONS: int
    PBKDF2_PWD_HASHER_SALT_LENGTH: int
    LOGGING_CONFIG: dict
    BALANCE_STATISTICS_YEARS: int
    DASHBOARD_JOINT_LIMITS_YEARS: int
    RUN_ON_HOST: str
    RUN_ON_PORT: int


def init_config(env_path: Optional[str] = None) -> Config:
    env = Env()
    env.read_env(env_path)

    with env.prefixed("MYFUNDS_WEB_"):
        return Config(
            SUPERUSER=env.str("SUPERUSER"),
            SECRET_KEY=env.str("SECRET_KEY"),
            DATABASE_PATH=env.str("DATABASE_PATH"),
            PBKDF2_PWD_HASHER_HASH_FUNC=env.str("PBKDF2_PWD_HASHER_HASH_FUNC"),
            PBKDF2_PWD_HASHER_ITERATIONS=env.int("PBKDF2_PWD_HASHER_ITERATIONS"),
            PBKDF2_PWD_HASHER_SALT_LENGTH=env.int("PBKDF2_PWD_HASHER_SALT_LENGTH"),
            LOGGING_CONFIG=env.json("LOGGING_CONFIG", "{}"),
            BALANCE_STATISTICS_YEARS=env.int("BALANCE_STATISTICS_YEARS", 5),
            DASHBOARD_JOINT_LIMITS_YEARS=env.int("DASHBOARD_JOINT_LIMITS_YEARS", 5),
            RUN_ON_HOST=env.str("RUN_ON_HOST", "localhost"),
            RUN_ON_PORT=env.int("RUN_ON_PORT", 8080),
        )
