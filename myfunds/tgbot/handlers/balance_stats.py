import calendar
from datetime import datetime
from typing import List
from typing import Tuple

import peewee as pw

from myfunds.core.constants import FundsDirection
from myfunds.core.models import Balance
from myfunds.core.models import BalanceLimit
from myfunds.core.models import Category
from myfunds.core.models import Currency
from myfunds.core.models import Transaction
from myfunds.tgbot.bot import HandlerContext
from myfunds.tgbot.utils import InlineKeyboard
from myfunds.tgbot.utils import calculate_available_years
from myfunds.tgbot.utils import make_date_range_by_year_and_month
from myfunds.web.utils import current_month
from myfunds.web.utils import current_year
from myfunds.web.utils import make_hrf_amount


def handler(ctx: HandlerContext) -> None:
    message_id = ctx.update["callback_query"]["message"]["message_id"]

    if ctx.command_args[0] == "set_balance":
        balances = (
            Balance.select()
            .join(Currency)
            .where(Balance.account == ctx.account)
            .order_by(Balance.name)
        )

        keyboard = InlineKeyboard(len(balances))
        for i, b in enumerate(balances):
            keyboard.add_button(i, b.name, f"/balance_stats set_year {b.id}")

        text = "\n\n".join(["*Balance Statistics*", "Selecting balance \\.\\.\\."])

        ctx.client.edit_message_text(
            text=text,
            chat_id=ctx.chat_id,
            message_id=message_id,
            parse_mode="MarkdownV2",
            reply_markup=keyboard.jsonify(),
        )

    elif ctx.command_args[0] == "set_year":
        balance = Balance.get_by_id(int(ctx.command_args[1]))
        currency = balance.currency

        years = calculate_available_years(ctx.config.MAX_YEARS_OF_STATISTICS)
        grouped_years = [years[i : i + 2] for i in range(0, len(years), 2)]

        keyboard = InlineKeyboard(len(grouped_years) + 1)
        keyboard.add_button(
            0,
            "Current year and month",
            f"/balance_stats build_report {balance.id} {current_year()} {current_month()}",  # noqa: E501
        )
        for i, years in enumerate(grouped_years):
            for y in years:
                keyboard.add_button(
                    (i + 1), str(y), f"/balance_stats set_month {balance.id} {y}"
                )

        text = "\n\n".join(
            [
                "*Balance Statistics*",
                f"`Balance: {balance.name} ({currency.code_alpha})`",
                "Selecting year \\.\\.\\.",
            ]
        )

        ctx.client.edit_message_text(
            text=text,
            chat_id=ctx.chat_id,
            message_id=message_id,
            parse_mode="MarkdownV2",
            reply_markup=keyboard.jsonify(),
        )
        return

    elif ctx.command_args[0] == "set_month":
        balance = Balance.get_by_id(int(ctx.command_args[1]))
        currency = balance.currency

        year = ctx.command_args[2]

        months = calendar.month_name

        # fmt: off
        keyboard = InlineKeyboard(3)
        keyboard.add_button(0, months[1], f"/balance_stats build_report {balance.id} {year} 1")  # noqa: E501
        keyboard.add_button(0, months[2], f"/balance_stats build_report {balance.id} {year} 2")  # noqa: E501
        keyboard.add_button(0, months[3], f"/balance_stats build_report {balance.id} {year} 3")  # noqa: E501
        keyboard.add_button(0, months[4], f"/balance_stats build_report {balance.id} {year} 4")  # noqa: E501
        keyboard.add_button(1, months[5], f"/balance_stats build_report {balance.id} {year} 5")  # noqa: E501
        keyboard.add_button(1, months[6], f"/balance_stats build_report {balance.id} {year} 6")  # noqa: E501
        keyboard.add_button(1, months[7], f"/balance_stats build_report {balance.id} {year} 7")  # noqa: E501
        keyboard.add_button(1, months[8], f"/balance_stats build_report {balance.id} {year} 8")  # noqa: E501
        keyboard.add_button(2, months[9], f"/balance_stats build_report {balance.id} {year} 9")  # noqa: E501
        keyboard.add_button(2, months[10], f"/balance_stats build_report {balance.id} {year} 10")  # noqa: E501
        keyboard.add_button(2, months[11], f"/balance_stats build_report {balance.id} {year} 11")  # noqa: E501
        keyboard.add_button(2, months[12], f"/balance_stats build_report {balance.id} {year} 12")  # noqa: E501
        # fmt: on

        text = "\n\n".join(
            [
                "*Balance Statistics*",
                f"`Balance: {balance.name} ({currency.code_alpha})`\n"
                f"`Year: {year}`",
                "Selecting month \\.\\.\\.",
            ]
        )

        ctx.client.edit_message_text(
            text=text,
            chat_id=ctx.chat_id,
            message_id=message_id,
            parse_mode="MarkdownV2",
            reply_markup=keyboard.jsonify(),
        )
        return

    elif ctx.command_args[0] == "build_report":
        balance = Balance.get_by_id(int(ctx.command_args[1]))
        currency = balance.currency
        year = int(ctx.command_args[2])
        month = int(ctx.command_args[3])

        stats_range = make_date_range_by_year_and_month(year, month)

        general_stats = calculate_general_stats(balance, stats_range)

        general_stats_table = []
        start_balance = make_hrf_amount(
            general_stats["start_balance"] or 0, currency.precision
        )
        expense = make_hrf_amount(general_stats["expense"] or 0, currency.precision)
        expense_pct = general_stats["expense_pct"]
        income = make_hrf_amount(general_stats["income"] or 0, currency.precision)
        end_balance = make_hrf_amount(
            general_stats["end_balance"] or 0, currency.precision
        )
        savings = make_hrf_amount(general_stats["savings"] or 0, currency.precision)
        savings_pct = general_stats["savings_pct"]

        general_stats_table.append(f"Start balance: {start_balance}")
        general_stats_table.append(f"Expense: {expense} ({expense_pct or 0.0}%)")
        general_stats_table.append(f"Income: {income}")
        general_stats_table.append(f"End balance: {end_balance}")
        general_stats_table.append(f"Savings: {savings} ({savings_pct or 0.0}%)")
        general_stats_table = "\n".join(general_stats_table)

        categories_stats = calculate_expense_categories_stats(balance, stats_range)

        categories_stats_table = []
        for i in categories_stats:
            categories_stats_table.append(
                f"`{i['name']}: {make_hrf_amount(i['amount'], currency.precision)}"
                f" ({i['amount_pct']}%)`"
            )
        categories_stats_table = "\n".join(categories_stats_table)

        text = []
        text.append("*Balance Statistics*")
        text.append(
            f"`Balance: {balance.name} ({currency.code_alpha})`\n"
            f"`Year: {year}`\n"
            f"`Month: {calendar.month_name[month]}`"
        )
        text.append(f"```\n{general_stats_table}```")
        if categories_stats_table != "":
            text.append(f"```\n{categories_stats_table}```")
        text = "\n\n".join(text)

        keyboard = InlineKeyboard(1)
        keyboard.add_button(0, "Remove", "/balance_stats remove")

        ctx.client.edit_message_text(
            text=text,
            chat_id=ctx.chat_id,
            message_id=message_id,
            parse_mode="MarkdownV2",
            reply_markup=keyboard.jsonify(),
        )
        return

    elif ctx.command_args[0] == "remove":
        ctx.client.delete_message(ctx.chat_id, message_id)
        return


def calculate_general_stats(
    balance: Balance, stats_range: Tuple[datetime, datetime]
) -> dict:
    year, month = stats_range[0].year, stats_range[0].month

    start_balance = calculate_start_balance(balance, stats_range)
    expense = calculate_expense(balance, stats_range)
    income = calculate_income(balance, stats_range)

    end_balance = None
    if year != current_year() or month != current_month():
        end_balance = calculate_end_balance(balance, stats_range)

    expense_pct, savings, savings_pct = None, None, None
    if start_balance is not None and expense is not None:
        expense_pct = round((expense / start_balance) * 100, 2)
        savings = start_balance - expense
        savings_pct = round((savings / start_balance) * 100, 2)

    return {
        "start_balance": start_balance,
        "expense": expense,
        "expense_pct": expense_pct,
        "income": income,
        "end_balance": end_balance,
        "savings": savings,
        "savings_pct": savings_pct,
    }


def calculate_expense_categories_stats(
    balance: Balance, stats_range: Tuple[datetime, datetime]
) -> List[dict]:
    # fmt: off
    categories = (
        Category
        .select(
            Category.id,
            Category.name,
            Category.color_sign,
            pw.fn.SUM(Transaction.amount).alias("amount"),
        )
        .join(Transaction)
        .where(
            (Category.account_id == balance.account_id)
            & (Category.direction == FundsDirection.EXPENSE)
            & (Transaction.balance_id == balance.id)
            & (Transaction.created_at.between(*stats_range))
        )
        .group_by(Category.id)
    )
    # fmt: on

    # fmt: off
    no_category_txns_amount = (
        Transaction
        .select(pw.fn.SUM(Transaction.amount))
        .where(
            (Transaction.balance == balance)
            & (Transaction.direction == FundsDirection.EXPENSE)
            & (Transaction.category.is_null())
            & (Transaction.created_at.between(*stats_range))
        )
        .scalar()
    )
    # fmt: on

    # fmt: off
    balance_limits = (
        BalanceLimit
        .select()
        .where(
            (BalanceLimit.balance == balance)
        )
    )
    # fmt: on

    expense = calculate_expense(balance, stats_range)

    categories_limit_amounts = {i.category_id: i.amount for i in balance_limits}

    result = []
    for category in categories:
        name = category.name
        amount = category.amount
        amount_pct = round((category.amount / expense) * 100, 2) if expense else None
        limit_amount = categories_limit_amounts.get(category.id)
        limit_amount_pct = None
        if limit_amount is not None:
            limit_amount_pct = round((category.amount / limit_amount) * 100, 2)

        result.append(
            {
                "name": name,
                "amount": amount,
                "amount_pct": amount_pct,
                "limit_amount": limit_amount,
                "limit_amount_pct": limit_amount_pct,
            }
        )

    if no_category_txns_amount is not None and no_category_txns_amount > 0:
        name = "No category"
        amount = no_category_txns_amount
        amount_pct = (
            round((no_category_txns_amount / expense) * 100, 2) if expense else None
        )
        limit_amount = None
        limit_amount_pct = None

        result.append(
            {
                "name": name,
                "amount": amount,
                "amount_pct": amount_pct,
                "limit_amount": limit_amount,
                "limit_amount_pct": limit_amount_pct,
            }
        )

    return list(reversed(sorted(result, key=lambda i: i["amount"])))


def calculate_start_balance(
    balance: Balance, stats_range: Tuple[datetime, datetime]
) -> int:
    # fmt: off
    last_txn_of_previous_month = (
        Transaction
        .select()
        .where(
            (Transaction.balance == balance)
            & (Transaction.created_at < stats_range[0])
        )
        .order_by(Transaction.created_at.desc())
        .first()
    )
    # fmt: on

    result = None
    if last_txn_of_previous_month is not None:
        result = last_txn_of_previous_month.balance_remainder

    return result


def calculate_end_balance(
    balance: Balance, stats_range: Tuple[datetime, datetime]
) -> int:
    # fmt: off
    last_txn_of_current_month = (
        Transaction
        .select()
        .where(
            (Transaction.balance == balance)
            & (Transaction.created_at.between(*stats_range))
        )
        .order_by(Transaction.created_at.desc())
        .first()
    )
    # fmt: on

    result = None
    if last_txn_of_current_month is not None:
        result = last_txn_of_current_month.balance_remainder

    return result


def calculate_income(balance: Balance, stats_range: Tuple[datetime, datetime]) -> int:
    # fmt: off
    return (
        Transaction
        .select(pw.fn.SUM(Transaction.amount))
        .where(
            (Transaction.balance == balance)
            & (Transaction.direction == FundsDirection.INCOME)
            & (Transaction.created_at.between(*stats_range))
        )
        .scalar()
    )
    # fmt: on


def calculate_expense(balance: Balance, stats_range: Tuple[datetime, datetime]) -> int:
    # fmt: off
    return (
        Transaction
        .select(pw.fn.SUM(Transaction.amount))
        .where(
            (Transaction.balance == balance)
            & (Transaction.direction == FundsDirection.EXPENSE)
            & (Transaction.created_at.between(*stats_range))
        )
        .scalar()
    )
    # fmt: on
