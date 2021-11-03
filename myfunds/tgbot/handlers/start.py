from myfunds.tgbot.bot import HandlerContext
from myfunds.tgbot.utils import InlineKeyboard


def handler(ctx: HandlerContext) -> None:
    keyboard = InlineKeyboard(3)
    keyboard.add_button(0, "Crypto balances", "/crypto_balances")
    keyboard.add_button(1, "Total budget", "/total_budget")
    keyboard.add_button(2, "Joint limits", "/joint_limits set_year")

    ctx.client.send_message(
        chat_id=ctx.chat_id,
        text="What information do you need?",
        reply_markup=keyboard.jsonify(),
    )
