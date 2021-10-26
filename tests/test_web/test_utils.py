import pytest

from myfunds.web import utils


@pytest.mark.parametrize(
    "currency_precision,result",
    [
        [0, r"^\d+$"],
        [1, r"^\d+(\.\d{1})?$"],
        [2, r"^\d+(\.\d{1,2})?$"],
        [3, r"^\d+(\.\d{1,3})?$"],
    ],
)
def test_make_amount_pattern(currency_precision, result):
    assert utils.make_amount_pattern(currency_precision) == result


@pytest.mark.parametrize(
    "currency_precision,result",
    [
        [0, "100"],
        [1, "100.0"],
        [2, "100.00"],
        [3, "100.000"],
    ],
)
def test_make_amount_placeholder(currency_precision, result):
    assert utils.make_amount_placeholder(currency_precision) == result


@pytest.mark.parametrize(
    "args,result",
    [
        [("100", 0), 100],
        [("100.5", 1), 1005],
        [("100.25", 2), 10025],
    ],
)
def test_amount_to_subunits(args, result):
    assert utils.amount_to_subunits(*args) == result
