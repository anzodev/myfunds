import peewee as pw
from prettytable import PLAIN_COLUMNS
from prettytable import PrettyTable

from myfunds.core.constants import CryptoDirection
from myfunds.core.models import Account
from myfunds.core.models import CryptoBalance
from myfunds.core.models import CryptoCurrency
from myfunds.core.models import CryptoTransaction
from myfunds.modules import cmc
from myfunds.tgbot.bot import HandlerContext
from myfunds.tgbot.utils import InlineKeyboard
from myfunds.tgbot.utils import get_logger
from myfunds.web import utils as web_utils


def build_report(account: Account) -> str:
    # fmt: off
    investments = (
        (
            CryptoTransaction
            .select(pw.fn.SUM(CryptoTransaction.amount))
            .where(
                (CryptoTransaction.account == account)
                & (CryptoTransaction.direction == CryptoDirection.INVESTMENT)
            )
            .scalar()
        )
        or 0.0
    )
    fixed_profit = (
        (
            CryptoTransaction
            .select(pw.fn.SUM(CryptoTransaction.amount))
            .where(
                (CryptoTransaction.account == account)
                & (CryptoTransaction.direction == CryptoDirection.FIXED_PROFIT)
            )
            .scalar()
        )
        or 0.0
    )
    # fmt: on

    balances = (
        CryptoBalance.select()
        .join(CryptoCurrency)
        .where(CryptoBalance.account == account)
        .order_by(CryptoBalance.name, CryptoCurrency.symbol)
    )

    currencies_ids = [i.currency.cmc_id for i in balances]
    try:
        prices = cmc.fetch_prices(currencies_ids, "USD")
    except Exception as e:
        logger = get_logger()
        logger.warning(f"Unexpected error while fetching cmc prices ({repr(e)}).")
        prices = {}

    balances_values = {}
    for b in balances:
        price, amount = prices.get(b.currency.cmc_id), None
        if price is not None:
            amount = round(float(web_utils.make_hrf_amount(b.quantity, 8)) * price, 2)

        balances_values[int(b.id)] = {"price": price, "amount": amount}

    investments_value = round(investments / 100, 2)
    fixed_profit_value = round(fixed_profit / 100, 2)
    current_value = 0.0
    current_profit_value = 0.0
    current_profit_value_pct = 0.0

    if balances_values:
        current_value = sum(i["amount"] for i in balances_values.values())

    if investments_value > 0:
        current_profit_value = round(current_value - investments_value, 2)
        current_profit_value_pct = round(
            (current_profit_value / investments_value) * 100, 2
        )

    # fmt: off
    general_table = PrettyTable()
    general_table.set_style(PLAIN_COLUMNS)
    general_table.add_row(["Investments:", f"{investments_value}$"])
    general_table.add_row(["Current value:", f"{current_value}$"])
    general_table.add_row(["Current profit:", f"{current_profit_value}$ ({current_profit_value_pct})%"])  # noqa: E501
    general_table.add_row(["Fixed profit:", f"{fixed_profit_value}$"])
    general_table.align = "l"
    # fmt: on

    balances_table = PrettyTable()
    balances_table.set_style(PLAIN_COLUMNS)
    for i in balances:
        quantity = round(i.quantity / (10 ** 8), 8)
        balances_table.add_row(
            [
                f"{i.name}:",
                f"{quantity} {i.currency.symbol} ({balances_values[i.id]['amount']}$)",
            ]
        )
    balances_table.align = "l"

    report = "\n\n".join(
        [
            "*Crypto Balances 123*",
            f"```\n{general_table.get_string(header=False, right_padding_width=1)}```",
            f"```\n{balances_table.get_string(header=False, right_padding_width=1)}```",
        ]
    )

    return report


def handler(ctx: HandlerContext) -> None:
    message_id = ctx.update["callback_query"]["message"]["message_id"]

    if len(ctx.command_args) > 0 and ctx.command_args[0] == "remove":
        ctx.client.delete_message(ctx.chat_id, message_id)
        return

    report = build_report(ctx.account)

    keyboard = InlineKeyboard(1)
    keyboard.add_button(0, "Remove", "/crypto_balances remove")

    ctx.client.edit_message_text(
        text=report,
        chat_id=ctx.chat_id,
        message_id=message_id,
        parse_mode="MarkdownV2",
        reply_markup=keyboard.jsonify(),
    )
