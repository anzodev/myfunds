import argparse
import logging.config as logging_config

from myfunds.domain import business
from myfunds.domain import models

from . import config
from . import create_app


# fmt: off
parser = argparse.ArgumentParser()
parser.add_argument("-e", "--env", dest="env_path", type=str, default=None, help="environment config file path")  # noqa: E501
# fmt: on

args = parser.parse_args()

web_config = config.from_env(args.env_path)
app = create_app(web_config)

if web_config.LOGGING_DICT_CONFIG and web_config.LOGGING_DICT_CONFIG != {}:
    logging_config.dictConfig(web_config.LOGGING_DICT_CONFIG)

database = business.init_database(web_config.DB_NAME)

with business.database_ctx(database):
    models.database.create_tables(business.model_list())
    app.run(
        host=web_config.RUN_HOST,
        port=web_config.RUN_PORT,
        use_reloader=web_config.RUN_USE_RELOADER,
        threaded=True,
    )
