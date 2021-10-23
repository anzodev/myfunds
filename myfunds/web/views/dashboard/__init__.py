from flask import Flask

from myfunds.web.views.dashboard.views import bp
from myfunds.web.views.dashboard.views import index  # noqa: F401
from myfunds.web.views.dashboard.views import joint_limits  # noqa: F401
from myfunds.web.views.dashboard.views import total_budget  # noqa: F401


def init_app(app: Flask) -> None:
    app.register_blueprint(bp)
