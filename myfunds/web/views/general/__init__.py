from flask import Flask

from myfunds.web.views.general.views import bp


def init_app(app: Flask) -> None:
    return app.register_blueprint(bp)
