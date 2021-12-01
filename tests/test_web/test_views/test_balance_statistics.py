from datetime import date as dt_date

import pytest

from myfunds.web.views.balances.balance.views import statistics


@pytest.mark.parametrize(
    "args,amount,percent,css_text_color",
    [
        ((100, None), None, None, None),
        ((0, 2000), 2000, 0.0, "text-success"),
        ((1180, 2000), 2000, 59.0, "text-success"),
        ((1200, 2000), 2000, 60.0, "text-warning"),
        ((1580, 2000), 2000, 79.0, "text-warning"),
        ((1600, 2000), 2000, 80.0, "text-danger"),
        ((2000, 2000), 2000, 100.0, "text-danger"),
        ((2002, 2000), 2000, -0.1, "text-danger"),
    ],
)
def test_init_expense_limit_params(args, amount, percent, css_text_color):
    expense_limit = statistics.init_expense_limit_params(*args)
    assert expense_limit.amount == amount
    assert expense_limit.percent == percent
    assert expense_limit.css_text_color == css_text_color


@pytest.mark.parametrize(
    "year,month,expected_result",
    [
        (2021, 1, (dt_date(2021, 1, 1), dt_date(2021, 2, 1))),
        (2021, 2, (dt_date(2021, 2, 1), dt_date(2021, 3, 1))),
        (2021, 3, (dt_date(2021, 3, 1), dt_date(2021, 4, 1))),
        (2021, 4, (dt_date(2021, 4, 1), dt_date(2021, 5, 1))),
        (2021, 5, (dt_date(2021, 5, 1), dt_date(2021, 6, 1))),
        (2021, 6, (dt_date(2021, 6, 1), dt_date(2021, 7, 1))),
        (2021, 7, (dt_date(2021, 7, 1), dt_date(2021, 8, 1))),
        (2021, 8, (dt_date(2021, 8, 1), dt_date(2021, 9, 1))),
        (2021, 9, (dt_date(2021, 9, 1), dt_date(2021, 10, 1))),
        (2021, 10, (dt_date(2021, 10, 1), dt_date(2021, 11, 1))),
        (2021, 11, (dt_date(2021, 11, 1), dt_date(2021, 12, 1))),
        (2021, 12, (dt_date(2021, 12, 1), dt_date(2022, 1, 1))),
    ],
)
def test_make_date_range_by_year_and_month(year, month, expected_result):
    assert statistics.make_date_range_by_year_and_month(year, month) == expected_result
