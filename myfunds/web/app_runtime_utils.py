from flask import current_app

from myfunds.tools.security import PBKDF2_PasswordHasher


def init_password_hasher() -> PBKDF2_PasswordHasher:
    return PBKDF2_PasswordHasher(
        hash_func=current_app.config["PBKDF2_PWD_HASHER_HASH_FUNC"],
        iterations=current_app.config["PBKDF2_PWD_HASHER_ITERATIONS"],
        salt_length=current_app.config["PBKDF2_PWD_HASHER_SALT_LENGTH"],
    )
