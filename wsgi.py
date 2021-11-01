import logging.config

from myfunds.core.models import db_proxy
from myfunds.web import create_app
from myfunds.web.config import init_config
from myfunds.web.utils import command_line_args


args = command_line_args()

config = init_config(args.env)
if config.LOGGING_CONFIG != {}:
    logging.config.dictConfig(config.LOGGING_CONFIG)

app = create_app(config)
db_proxy.initialize(app.config["DATABASE"])
