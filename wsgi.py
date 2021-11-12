import logging.config
import os

from myfunds.config import init_config
from myfunds.config import init_env_parser
from myfunds.core.models import db_proxy
from myfunds.web import create_app
from myfunds.web.utils import disable_werkzeug_logs


parser = init_env_parser()
args = parser.parse_args()

config = init_config(args.env)
if config.LOGGING_CONFIG != {}:
    logging.config.dictConfig(config.LOGGING_CONFIG)

app = create_app(config)
db_proxy.initialize(app.config["DATABASE"])


if __name__ == "__main__":
    disable_werkzeug_logs()

    app.templates_auto_reload = True
    app.jinja_options["auto_reload"] = True

    host, port = app.config["WEB_RUN_ON_HOST"], app.config["WEB_RUN_ON_PORT"]
    app.run(host=host, port=port, use_reloader=True, threaded=True)
