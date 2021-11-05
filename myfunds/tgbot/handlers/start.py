from myfunds.tgbot.bot import HandlerContext
from myfunds.tgbot.utils import InlineKeyboard


def handler(ctx: HandlerContext) -> None:
    keyboard = InlineKeyboard(2)
    keyboard.add_button(0, "Crypto Balances", "/crypto_balances")
    keyboard.add_button(0, "Total Budget", "/total_budget")
    keyboard.add_button(1, "Joint Limits", "/joint_limits set_year")
    keyboard.add_button(1, "Balance Statistics", "/balance_stats set_balance")

    ctx.client.delete_message(ctx.chat_id, ctx.update["message"]["message_id"])
    ctx.client.send_message(
        chat_id=ctx.chat_id,
        text="What are you interested for?",
        reply_markup=keyboard.jsonify(),
    )
