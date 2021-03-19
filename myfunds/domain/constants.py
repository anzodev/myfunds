from collections import namedtuple


def _constants(**variables) -> namedtuple:
    return namedtuple(
        typename="Constant",
        field_names=list(variables.keys()),
    )(**variables)


TransactionType = _constants(
    REPLENISHMENT="replenishment",
    WITHDRAWAL="withdrawal",
)
