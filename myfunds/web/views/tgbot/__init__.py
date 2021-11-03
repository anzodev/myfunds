from flask import Flask

from myfunds.web.views.tgbot.views import bp


def init_app(app: Flask) -> None:
    app.register_blueprint(bp)
