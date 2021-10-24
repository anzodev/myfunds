from flask import Flask

from myfunds.web.views import access
from myfunds.web.views import accounts
from myfunds.web.views import balances
from myfunds.web.views import categories
from myfunds.web.views import crypto
from myfunds.web.views import crypto_currenices
from myfunds.web.views import currencies
from myfunds.web.views import dashboard
from myfunds.web.views import general
from myfunds.web.views import joint_limits


def init_app(app: Flask) -> None:
    access.init_app(app)
    accounts.init_app(app)
    balances.init_app(app)
    categories.init_app(app)
    crypto.init_app(app)
    crypto_currenices.init_app(app)
    currencies.init_app(app)
    dashboard.init_app(app)
    general.init_app(app)
    joint_limits.init_app(app)
