from flask import Flask

from myfunds.web.views.joint_limits import views  # noqa: F401
from myfunds.web.views.joint_limits.limit.views import bp as limit_bp
from myfunds.web.views.joint_limits.limit.views import index  # noqa: F401
from myfunds.web.views.joint_limits.limit.views import participants  # noqa: F401, E501
from myfunds.web.views.joint_limits.views import bp as limits_bp


def init_app(app: Flask) -> None:
    limits_bp.register_blueprint(limit_bp, name="i")
    return app.register_blueprint(limits_bp)
