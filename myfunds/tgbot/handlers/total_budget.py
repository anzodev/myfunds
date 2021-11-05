from typing import Optional

from myfunds.core.models import Account
from myfunds.core.models import Balance
from myfunds.core.models import CryptoBalance
from myfunds.core.models import CryptoCurrency
from myfunds.core.models import Currency
from myfunds.modules import cmc
from myfunds.modules import convertmymoney
from myfunds.tgbot.bot import HandlerContext
from myfunds.tgbot.utils import InlineKeyboard
from myfunds.tgbot.utils import get_logger
from myfunds.web import utils as web_utils


def handler(ctx: HandlerContext) -> None:
    message_id = ctx.update["callback_query"]["message"]["message_id"]

    if len(ctx.command_args) > 0 and ctx.command_args[0] == "remove":
        ctx.client.delete_message(ctx.chat_id, message_id)
        return

    report = build_report(ctx.account)
    if report is None:
        report = "*Total Budget*\n\nNo data\\."

    keyboard = InlineKeyboard(1)
    keyboard.add_button(0, "Remove", "/total_budget remove")

    ctx.client.edit_message_text(
        text=report,
        chat_id=ctx.chat_id,
        message_id=message_id,
        parse_mode="MarkdownV2",
        reply_markup=keyboard.jsonify(),
    )


def build_report(account: Account) -> Optional[str]:
    common_balances = []

    balances = (
        Balance.select()
        .join(Currency)
        .where(Balance.account == account)
        .order_by(Balance.name)
    )

    crypto_balances = (
        CryptoBalance.select()
        .join(CryptoCurrency)
        .where(CryptoBalance.account == account)
        .order_by(CryptoBalance.name, CryptoCurrency.symbol)
    )

    if not balances and not common_balances:
        return

    try:
        exchange_rates = convertmymoney.fetch_exchange_rates()
    except Exception as e:
        logger = get_logger()
        logger.warning(f"Fethcing exchange rates occures error ({repr(e)}).")
        exchange_rates = {}

    for b in balances:
        item = {}
        item["balance_name"] = b.name
        item["currency_code"] = b.currency.code_alpha
        item["amount"] = float(
            web_utils.make_hrf_amount(b.amount, b.currency.precision)
        )

        rate = exchange_rates.get(b.currency.code_alpha)
        if rate is not None:
            item["converted_amount"] = round(item["amount"] / rate, 2)
        else:
            item["converted_amount"] = None

        common_balances.append(item)

    currencies_ids = [b.currency.cmc_id for b in crypto_balances]

    try:
        prices = cmc.fetch_prices(currencies_ids)
    except Exception as e:
        logger = get_logger()
        logger.warning(f"Fethcing prices occures error ({repr(e)}).")
        prices = {}

    for b in crypto_balances:
        item = {}
        item["balance_name"] = b.name
        item["currency_code"] = b.currency.symbol
        item["amount"] = float(web_utils.make_hrf_amount(b.quantity, 8))

        price = prices.get(b.currency.cmc_id)
        if price is not None:
            item["converted_amount"] = round(item["amount"] * price, 2)
        else:
            item["converted_amount"] = None

        common_balances.append(item)

    total_converted_amount = round(
        sum(
            [
                i["converted_amount"]
                for i in common_balances
                if i["converted_amount"] is not None
            ]
        ),
        2,
    )

    # fmt: off
    total_amount = (
        [f"{total_converted_amount} USD"]
        + [
            f'{i["amount"]} {i["currency_code"]}'
            for i in common_balances if i["converted_amount"] is None
        ]
    )
    # fmt: on

    total_amount = " + ".join(total_amount)

    balances_rows = []
    for i in common_balances:
        converted_amount = (
            f'{i["converted_amount"]} USD' if i["converted_amount"] else "-"
        )
        balances_rows.append(
            f'{i["balance_name"]}: {i["amount"]} {i["currency_code"]} '
            f"({converted_amount})"
        )

    balances_rows = "\n".join(balances_rows)
    report = (
        f"*Total Budget*\n\n```\n{balances_rows}\n\nTotal amount: {total_amount}```"
    )

    return report
