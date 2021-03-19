import argparse
import json
import logging.config as logging_cfg

from myfunds.domain import business
from myfunds.domain import models

from . import config
from . import create_app


# fmt: off
parser = argparse.ArgumentParser()
parser.add_argument("-e", "--env", dest="env_path", type=str, default=None, help="environment config file path")  # noqa: E501
# fmt: on

args = parser.parse_args()

cfg = config.from_env(args.env_path)
app = create_app(cfg)

if cfg.LOGGING_DICT_CONFIG and cfg.LOGGING_DICT_CONFIG != "{}":
    logging_cfg.dictConfig(json.loads(cfg.LOGGING_DICT_CONFIG))

database = business.init_database(cfg.DB_NAME)

with business.database_ctx(database):
    models.database.create_tables(business.model_list())
    app.run(
        host=cfg.RUN_HOST,
        port=cfg.RUN_PORT,
        use_reloader=cfg.RUN_USE_RELOADER,
        threaded=True,
    )
