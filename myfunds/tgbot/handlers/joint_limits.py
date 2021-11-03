import calendar
from datetime import date
from datetime import datetime
from typing import List
from typing import Tuple

import peewee as pw
from prettytable import PLAIN_COLUMNS
from prettytable import PrettyTable

from myfunds.core.constants import FundsDirection
from myfunds.core.models import Account
from myfunds.core.models import Balance
from myfunds.core.models import Category
from myfunds.core.models import JointLimit
from myfunds.core.models import JointLimitParticipant
from myfunds.core.models import Transaction
from myfunds.tgbot.bot import HandlerContext
from myfunds.tgbot.utils import InlineKeyboard
from myfunds.web import utils as web_utils


def calculate_available_years(max_years: int) -> List[int]:
    current_year = date.today().year
    return [current_year] + [current_year - i for i in range(1, max_years + 1)]


def make_date_range_by_year_and_month(year: int, month: int) -> Tuple[date, date]:
    until_year = year if month < 12 else year + 1
    until_month = month + 1 if month < 12 else 1
    return (date(year, month, 1), date(until_year, until_month, 1))


def prepare_joint_limits_data(
    account: Account, stats_range: Tuple[datetime, datetime]
) -> List[dict]:
    # fmt: off
    categories_ids_query = (
        Category
        .select(Category.id)
        .where(
            (Category.account == account)
            & (Category.direction == FundsDirection.EXPENSE)
        )
    )
    # fmt: on
    categories_ids = [i.id for i in categories_ids_query]

    limits = (
        JointLimit.select()
        .join(JointLimitParticipant)
        .where(JointLimitParticipant.category_id.in_(categories_ids))
        .group_by(JointLimit.id)
    )

    result = []

    for limit in limits:
        # fmt: off
        participants_query = (
            JointLimitParticipant
            .select()
            .where(JointLimitParticipant.limit == limit)
        )
        # fmt: on

        currency = limit.currency

        participants = []
        for p in participants_query:
            category = p.category
            account = category.account

            # fmt: off
            balances = (
                Balance
                .select(
                    Balance,
                    pw.fn.SUM(Transaction.amount).alias("expense_amount"),
                )
                .join(Transaction, pw.JOIN.LEFT_OUTER)
                .where(
                    (Balance.account == account)
                    & (Balance.currency == currency)
                    & (Transaction.category == category)
                    & (Transaction.created_at.between(*stats_range))
                )
                .group_by(Balance.id)
            )
            # fmt: on

            if not balances:
                continue

            total_expense = sum([i.expense_amount for i in balances] + [0])

            participants.append({"account": account, "total_expense": total_expense})

        if len(participants) == 0:
            continue

        total_expense = sum([p["total_expense"] for p in participants])
        total_expense_pct = round((total_expense / limit.amount) * 100, 2)
        if total_expense_pct > 100:
            total_expense_pct = round(100 - total_expense_pct, 2)

        result.append(
            {
                "limit": limit,
                "currency": currency,
                "participants": participants,
                "total_expense": total_expense,
                "total_expense_pct": total_expense_pct,
            }
        )

    return result


def handler(ctx: HandlerContext) -> None:
    message_id = ctx.update["callback_query"]["message"]["message_id"]

    if ctx.command_args[0] == "remove":
        ctx.client.delete_message(ctx.chat_id, message_id)
        return

    elif ctx.command_args[0] == "set_year":
        years = calculate_available_years(ctx.config.MAX_YEARS_OF_STATISTICS)
        grouped_years = [years[i : i + 6] for i in range(0, len(years), 6)]

        keyboard = InlineKeyboard(len(grouped_years))
        for i, years in enumerate(grouped_years):
            for y in years:
                keyboard.add_button(i, str(y), f"/joint_limits set_month {y}")

        text = "\n\n".join(["*Joint Limits*", "Select year\\."])

        ctx.client.edit_message_text(
            text=text,
            chat_id=ctx.chat_id,
            message_id=message_id,
            parse_mode="MarkdownV2",
            reply_markup=keyboard.jsonify(),
        )
        return

    elif ctx.command_args[0] == "set_month":
        months = calendar.month_name
        year = ctx.command_args[1]

        keyboard = InlineKeyboard(3)
        keyboard.add_button(0, months[1], f"/joint_limits build_report {year} 1")
        keyboard.add_button(0, months[2], f"/joint_limits build_report {year} 2")
        keyboard.add_button(0, months[3], f"/joint_limits build_report {year} 3")
        keyboard.add_button(0, months[4], f"/joint_limits build_report {year} 4")
        keyboard.add_button(1, months[5], f"/joint_limits build_report {year} 5")
        keyboard.add_button(1, months[6], f"/joint_limits build_report {year} 6")
        keyboard.add_button(1, months[7], f"/joint_limits build_report {year} 7")
        keyboard.add_button(1, months[8], f"/joint_limits build_report {year} 8")
        keyboard.add_button(2, months[9], f"/joint_limits build_report {year} 9")
        keyboard.add_button(2, months[10], f"/joint_limits build_report {year} 10")
        keyboard.add_button(2, months[11], f"/joint_limits build_report {year} 11")
        keyboard.add_button(2, months[12], f"/joint_limits build_report {year} 12")

        text = "\n\n".join(["*Joint Limits*", f"Year {year}, select month\\."])

        ctx.client.edit_message_text(
            text=text,
            chat_id=ctx.chat_id,
            message_id=message_id,
            parse_mode="MarkdownV2",
            reply_markup=keyboard.jsonify(),
        )
        return

    elif ctx.command_args[0] == "build_report":
        year, month = int(ctx.command_args[1]), int(ctx.command_args[2])
        stats_range = make_date_range_by_year_and_month(year, month)
        joint_limits_data = prepare_joint_limits_data(ctx.account, stats_range)

        keyboard = InlineKeyboard(1)
        keyboard.add_button(0, "Remove", "/joint_limits remove")

        if len(joint_limits_data) == 0:
            text = "\n\n".join(
                ["*Joint Limits*", f"No data \\({year}\\-{month:>02}\\)\\."]
            )
            ctx.client.edit_message_text(
                text=text,
                chat_id=ctx.chat_id,
                message_id=message_id,
                parse_mode="MarkdownV2",
                reply_markup=keyboard.jsonify(),
            )
            return

        limits_tables = []
        for i in joint_limits_data:
            ccy_precision = i["currency"].precision
            total_expense = web_utils.make_hrf_amount(i["total_expense"], ccy_precision)
            limit_amount = web_utils.make_hrf_amount(i["limit"].amount, ccy_precision)

            table = PrettyTable()
            table.set_style(PLAIN_COLUMNS)
            table.add_row(["Name:", i["limit"].name])
            table.add_row(["Currency:", i["currency"].code_alpha])
            for p in i["participants"]:
                table.add_row(
                    [
                        f'User {p["account"].username}:',
                        web_utils.make_hrf_amount(p["total_expense"], ccy_precision),
                    ]
                )
            table.add_row(["Total expense:", total_expense])
            table.add_row(["Limit:", f"{limit_amount} ({i['total_expense_pct']}%)"])
            table.align = "l"

            limits_tables.append(table)

        text = ["*Joint Limits*"]
        for t in limits_tables:
            text.append(f"```\n{t.get_string(header=False, right_padding_width=1)}```")
        text = "\n\n".join(text)

        ctx.client.edit_message_text(
            text=text,
            chat_id=ctx.chat_id,
            message_id=message_id,
            parse_mode="MarkdownV2",
            reply_markup=keyboard.jsonify(),
        )
