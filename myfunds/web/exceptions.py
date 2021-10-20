import json

from wtforms import Form


class BaseError(Exception):
    ...


class FormValidationError(BaseError):
    def __init__(self, form: Form, redirect_url: str):
        super().__init__(json.dumps(form.errors))
        self.redirect_url = redirect_url
