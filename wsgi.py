import logging.config

from myfunds.web import create_app
from myfunds.web.config import init_config
from myfunds.web.utils import disable_werkzeug_logs
from myfunds.web.utils import parse_env_parser


disable_werkzeug_logs()

args = parse_env_parser()

config = init_config(args.env)
if config.LOGGING_CONFIG != {}:
    logging.config.dictConfig(config.LOGGING_CONFIG)

app = create_app(config)
