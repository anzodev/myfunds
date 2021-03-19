import flask

from . import api
from . import config
from . import template_filters


# from . import hooks


def create_app(cfg: config.Config):
    app = flask.Flask(__name__)
    app.config.from_object(cfg)

    api.forms.init_app(app)
    api.pages.init_app(app)
    # hooks.init_app(app)
    template_filters.init_app(app)

    return app
