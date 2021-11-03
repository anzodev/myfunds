import logging.config

from myfunds.config import init_config
from myfunds.config import init_env_parser
from myfunds.core.models import db_proxy
from myfunds.web import create_app


parser = init_env_parser()
args = parser.parse_args()

config = init_config(args.env)
if config.LOGGING_CONFIG != {}:
    logging.config.dictConfig(config.LOGGING_CONFIG)

app = create_app(config)
db_proxy.initialize(app.config["DATABASE"])
