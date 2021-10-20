from typing import Mapping
from typing import Type

from flask import current_app
from wtforms import Form

from myfunds.modules.security import PBKDF2_PasswordHasher
from myfunds.web import notify
from myfunds.web.exceptions import FormValidationError


def init_password_hasher() -> PBKDF2_PasswordHasher:
    return PBKDF2_PasswordHasher(
        hash_func=current_app.config["PBKDF2_PWD_HASHER_HASH_FUNC"],
        iterations=current_app.config["PBKDF2_PWD_HASHER_ITERATIONS"],
        salt_length=current_app.config["PBKDF2_PWD_HASHER_SALT_LENGTH"],
    )


def init_and_validate_form(
    form_cls: Type[Form], data: Mapping, redirect_url: str
) -> Form:
    form = form_cls(data)
    if not form.validate():
        notify.error("Form data validation error.")
        raise FormValidationError(form, redirect_url)
    return form
