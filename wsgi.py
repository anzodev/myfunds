import logging.config

from myfunds.web import create_app
from myfunds.web.config import init_config
from myfunds.web.utils import disable_werkzeug_logs
from myfunds.web.utils import parse_env_parser


args = parse_env_parser()
config = init_config(args.env)
app = create_app(config)


if __name__ == "__main__":
    disable_werkzeug_logs()

    if config.LOGGING_CONFIG != {}:
        logging.config.dictConfig(config.LOGGING_CONFIG)

    app.templates_auto_reload = True
    app.jinja_options["auto_reload"] = True
    app.run(use_reloader=True, threaded=True)
