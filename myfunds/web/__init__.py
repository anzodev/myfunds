import flask

from myfunds.web import context_processor
from myfunds.web import database
from myfunds.web import hooks
from myfunds.web import views
from myfunds.web.config import Config


def create_app(config: Config) -> flask.Flask:
    app = flask.Flask(__name__)
    app.config.from_object(config)

    database.init_app(app)
    views.init_app(app)
    hooks.init_app(app)
    context_processor.init_app(app)

    return app
