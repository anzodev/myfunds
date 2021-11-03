import flask

from myfunds.config import Config
from myfunds.database import init_database
from myfunds.web import context_processor
from myfunds.web import hooks
from myfunds.web import views


def create_app(config: Config) -> flask.Flask:
    app = flask.Flask(__name__)

    app.config["SECRET_KEY"] = config.WEB_SECRET_KEY
    app.config["DATABASE"] = init_database(config.DATABASE_PATH)
    app.config.from_object(config)

    views.init_app(app)
    hooks.init_app(app)
    context_processor.init_app(app)

    return app
