import peewee as pw

from myfunds.core.constants import CryptoDirection
from myfunds.core.models import Account
from myfunds.core.models import CryptoBalance
from myfunds.core.models import CryptoCurrency
from myfunds.core.models import CryptoTransaction
from myfunds.modules import cmc
from myfunds.tgbot.bot import HandlerContext
from myfunds.tgbot.utils import InlineKeyboard
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

    prices = cmc.fetch_prices(currencies_ids, "USD")

    balances_values = {}
    for b in balances:
        price = prices[b.currency.cmc_id]
        # fmt: off
        amount = (
            float(web_utils.make_hrf_amount(b.quantity, 8))
            * price
        )
        amount = round(amount, 2)
        # fmt: on

        balances_values[b.id] = {"price": price, "amount": amount}

    investments_value = round(investments / 100, 2)
    fixed_profit_value = round(fixed_profit / 100, 2)
    current_value = 0.0
    current_profit_value = 0.0
    current_profit_value_pct = 0.0
    total_profit_value = 0.0
    total_profit_value_pct = 0.0

    if balances_values:
        current_value = round(sum(i["amount"] for i in balances_values.values()), 2)

    if investments_value > 0:
        current_profit_value = round(current_value - investments_value, 2)
        current_profit_value_pct = round(
            (current_profit_value / investments_value) * 100, 2
        )
        total_profit_value = round(current_profit_value + fixed_profit_value, 2)
        total_profit_value_pct = round(
            (total_profit_value / investments_value) * 100, 2
        )

    unique_currencies = sorted(
        set(b.currency for b in balances),
        key=lambda c: c.symbol,
    )
    currencies_prices_table = []
    for c in unique_currencies:
        currencies_prices_table.append(f"{c.symbol}: {prices[c.cmc_id]}")
    currencies_prices_table = "\n".join(currencies_prices_table)

    # fmt: off
    general_table = []
    general_table.append(f"Investments: {investments_value}$")
    general_table.append(f"Current value: {current_value}$")
    general_table.append(f"Fixed profit: {fixed_profit_value}$")
    general_table.append(f"Current profit: {current_profit_value}$ ({current_profit_value_pct})%")  # noqa: E501
    general_table.append(f"Total profit: {total_profit_value}$ ({total_profit_value_pct})%")  # noqa: E501
    general_table = "\n".join(general_table)
    # fmt: on

    balances_table = []
    for i in balances:
        quantity = round(i.quantity / (10 ** 8), 8)
        balances_table.append(
            f"{i.name}: {quantity} {i.currency.symbol}"
            f" ({balances_values[i.id]['amount']}$)",
        )
    balances_table = "\n".join(balances_table)

    report = []
    report.append("*Crypto Balances*")
    report.append(f"```\n{currencies_prices_table}```")
    report.append(f"```\n{general_table}```")
    report.append(f"```\n{balances_table}```")
    report = "\n\n".join(report)

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
