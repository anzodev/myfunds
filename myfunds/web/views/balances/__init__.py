from flask import Flask

from myfunds.web.views.balances import views  # noqa: F401
from myfunds.web.views.balances.balance.views import bp as balance_bp
from myfunds.web.views.balances.balance.views import index  # noqa: F401
from myfunds.web.views.balances.balance.views import replenishment  # noqa: F401
from myfunds.web.views.balances.balance.views import statistics  # noqa: F401
from myfunds.web.views.balances.balance.views import transactions  # noqa: F401
from myfunds.web.views.balances.balance.views import withdrawal  # noqa: F401
from myfunds.web.views.balances.views import bp as balances_bp


def init_app(app: Flask) -> None:
    balances_bp.register_blueprint(balance_bp, name="i")
    app.register_blueprint(balances_bp)
