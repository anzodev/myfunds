import argparse
import logging.config as logging_config

from myfunds.domain import models

from . import config
from . import create_app
from . import database


# fmt: off
parser = argparse.ArgumentParser()
parser.add_argument("-e", "--env", dest="env_path", type=str, default=None, help="environment config file path")  # noqa: E501
# fmt: on

args = parser.parse_args()

web_config = config.from_env(args.env_path)
app = create_app(web_config)

if web_config.LOGGING_DICT_CONFIG and web_config.LOGGING_DICT_CONFIG != {}:
    logging_config.dictConfig(web_config.LOGGING_DICT_CONFIG)

db = database.init_database(web_config.DB_NAME)
models.database.initialize(db)
models.database.create_tables(models.get_models())

app.run(
    host=web_config.RUN_HOST,
    port=web_config.RUN_PORT,
    use_reloader=web_config.RUN_USE_RELOADER,
    threaded=True,
)
