import argparse
import json
import logging.config as logging_config

from myfunds import web
from myfunds.domain import business
from myfunds.domain import models
from myfunds.web import config


# fmt: off
parser = argparse.ArgumentParser()
parser.add_argument("-e", "--env", dest="env_path", type=str, default=None, help="environment config file path")  # noqa: E501
# fmt: on

args = parser.parse_args()
web_config = config.from_env(args.env_path)

if web_config.LOGGING_DICT_CONFIG and web_config.LOGGING_DICT_CONFIG != "{}":
    logging_config.dictConfig(json.loads(web_config.LOGGING_DICT_CONFIG))

database = business.init_database(web_config.DB_NAME)
models.database.initialize(database)

app = web.create_app(web_config)
