from datetime import datetime
from typing import Optional

import peewee as pw

from myfunds.core.constants import FundsDirection
from myfunds.core.models import Balance
from myfunds.core.models import Category
from myfunds.core.models import Transaction
from myfunds.core.models import db_proxy
from myfunds.modules import check


def _calculate_common_balance_remainder_for_new_transaction(
    balance: Balance,
    created_at: datetime,
):
    common_balance_remainder = 0

    # fmt: off
    last_txn = (
        Transaction.select()
        .where(
            (Transaction.balance == balance)
            & (Transaction.created_at < created_at)
        )
        .order_by(Transaction.created_at.desc())
        .first()
    )
    # fmt: on
    if last_txn is not None:
        common_balance_remainder += last_txn.balance_remainder

    # fmt: off
    sametime_replenishments_sum = (
        Transaction
        .select(
            pw.fn.SUM(Transaction.amount).alias("value")
        )
        .where(
            (Transaction.balance == balance)
            & (Transaction.direction == FundsDirection.INCOME)
            & (Transaction.created_at == created_at)
        )
        .group_by(Transaction.created_at)
        .first()
    )
    # fmt: on
    if sametime_replenishments_sum is not None:
        common_balance_remainder += sametime_replenishments_sum.value

    # fmt: off
    sametime_withdrawals_sum = (
        Transaction
        .select(
            pw.fn.SUM(Transaction.amount).alias("value")
        )
        .where(
            (Transaction.balance == balance)
            & (Transaction.direction == FundsDirection.EXPENSE)
            & (Transaction.created_at == created_at)
        )
        .group_by(Transaction.created_at)
        .first()
    )
    # fmt: on
    if sametime_withdrawals_sum is not None:
        common_balance_remainder -= sametime_withdrawals_sum.value

    return common_balance_remainder


def make_replenishment(
    balance: Balance,
    amount: int,
    category: Optional[Category] = None,
    comment: Optional[str] = None,
    created_at: Optional[datetime] = None,
) -> Transaction:
    check.value(balance, [check.is_instance(Balance)])
    check.value(amount, [check.is_instance(int), check.gt(0)])
    if category is not None:
        check.value(category, [check.is_instance(Category)])
        check.value(category.direction, [check.eq(FundsDirection.INCOME)])
        check.value(category.account_id, [check.eq(balance.account_id)])
    if comment is not None:
        check.value(comment, [check.is_instance(str)])
    if created_at is not None:
        check.value(created_at, [check.is_instance(datetime)])

    created_at = created_at or datetime.now()

    with db_proxy.atomic():
        balance_remainder = _calculate_common_balance_remainder_for_new_transaction(
            balance, created_at
        )
        balance_remainder += amount

        txn = Transaction.create(
            balance=balance,
            balance_remainder=balance_remainder,
            direction=FundsDirection.INCOME,
            category=category,
            amount=amount,
            comment=comment,
            created_at=created_at,
        )

        # fmt: off
        (
            Balance
            .update(amount=(Balance.amount + amount))
            .where(Balance.id == balance.id)
            .execute()
        )
        # fmt: on

        # fmt: off
        (
            Transaction
            .update(balance_remainder=balance_remainder)
            .where(
                (Transaction.balance == balance)
                & (Transaction.created_at == created_at)
            )
            .execute()
        )
        # fmt: on

        # fmt: off
        (
            Transaction
            .update(
                balance_remainder=(Transaction.balance_remainder + amount)
            )
            .where(
                (Transaction.balance == balance)
                & (Transaction.created_at > created_at)
            )
            .execute()
        )
        # fmt: on

        return txn


def make_withdrawal(
    balance: Balance,
    amount: int,
    category: Optional[Category] = None,
    comment: Optional[str] = None,
    created_at: Optional[datetime] = None,
) -> Transaction:
    check.value(balance, [check.is_instance(Balance)])
    check.value(amount, [check.is_instance(int), check.gt(0)])
    if category is not None:
        check.value(category, [check.is_instance(Category)])
        check.value(category.direction, [check.eq(FundsDirection.EXPENSE)])
        check.value(category.account_id, [check.eq(balance.account_id)])
    if comment is not None:
        check.value(comment, [check.is_instance(str)])
    if created_at is not None:
        check.value(created_at, [check.is_instance(datetime)])

    created_at = created_at or datetime.now()

    with db_proxy.atomic():
        balance_remainder = _calculate_common_balance_remainder_for_new_transaction(
            balance, created_at
        )
        balance_remainder -= amount

        txn = Transaction.create(
            balance=balance,
            balance_remainder=balance_remainder,
            direction=FundsDirection.EXPENSE,
            category=category,
            amount=amount,
            comment=comment,
            created_at=created_at,
        )

        # fmt: off
        (
            Balance
            .update(amount=(Balance.amount - amount))
            .where(Balance.id == balance.id)
            .execute()
        )
        # fmt: on

        # fmt: off
        (
            Transaction
            .update(balance_remainder=balance_remainder)
            .where(
                (Transaction.balance == balance)
                & (Transaction.created_at == created_at)
            )
            .execute()
        )
        # fmt: on

        # fmt: off
        (
            Transaction
            .update(
                balance_remainder=(Transaction.balance_remainder - amount)
            )
            .where(
                (Transaction.balance == balance)
                & (Transaction.created_at > created_at)
            )
            .execute()
        )
        # fmt: on

        return txn


def remove_transaction(txn: Transaction) -> None:
    check.value(txn, [check.is_instance(Transaction)])

    signed_amount = (
        -txn.amount if txn.direction == FundsDirection.INCOME else txn.amount
    )

    with db_proxy.atomic():
        # fmt: off
        (
            Balance
            .update(amount=(Balance.amount + signed_amount))
            .where(Balance.id == txn.balance_id)
            .execute()
        )
        # fmt: on

        # fmt: off
        (
            Transaction
            .update(balance_remainder=(Transaction.balance_remainder + signed_amount))
            .where(
                (Transaction.balance_id == txn.balance_id)
                & (Transaction.created_at >= txn.created_at)
            )
            .execute()
        )
        # fmt: on

        txn.delete_instance()
