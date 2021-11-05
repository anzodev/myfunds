import atexit
import logging.config

from myfunds.config import init_config
from myfunds.config import init_env_parser
from myfunds.core.models import db_proxy
from myfunds.database import init_database
from myfunds.tgbot.bot import Bot
from myfunds.tgbot.handlers import balance_stats
from myfunds.tgbot.handlers import crypto_balances
from myfunds.tgbot.handlers import joint_limits
from myfunds.tgbot.handlers import start
from myfunds.tgbot.handlers import total_budget
from myfunds.tgbot.utils import get_logger


@atexit.register
def log_exit():
    logger = get_logger()
    logger.info("Bot stops working, exit.")


def main() -> None:
    parser = init_env_parser()
    args = parser.parse_args()

    config = init_config(args.env)
    if config.LOGGING_CONFIG != {}:
        logging.config.dictConfig(config.LOGGING_CONFIG)

    db = init_database(config.DATABASE_PATH)
    db_proxy.initialize(db)

    bot = Bot(config)
    bot.add_handler("/start", start.handler)
    bot.add_handler("/crypto_balances", crypto_balances.handler)
    bot.add_handler("/total_budget", total_budget.handler)
    bot.add_handler("/joint_limits", joint_limits.handler)
    bot.add_handler("/balance_stats", balance_stats.handler)
    bot.run()


if __name__ == "__main__":
    main()
