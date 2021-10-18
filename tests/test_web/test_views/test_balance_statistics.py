import pytest

from myfunds.web.views.balances.balance.views import statistics


@pytest.mark.parametrize(
    "args,value,percent,css_text_color",
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
def test_init_month_limit(args, value, percent, css_text_color):
    month_limit = statistics.init_month_limit(*args)
    assert month_limit.value == value
    assert month_limit.percent == percent
    assert month_limit.css_text_color == css_text_color
