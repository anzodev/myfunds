from flask import Flask

from myfunds.web.views import access
from myfunds.web.views import accounts
from myfunds.web.views import balances
from myfunds.web.views import categories
from myfunds.web.views import currencies
from myfunds.web.views import general


def init_app(app: Flask) -> None:
    access.init_app(app)
    general.init_app(app)
    balances.init_app(app)
    categories.init_app(app)
    accounts.init_app(app)
    currencies.init_app(app)
