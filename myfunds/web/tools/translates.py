from myfunds.domain.constants import TransactionType


N_A = "н/д"

TXN_TYPE_REPLENISHMENT = "Пополнение"
TXN_TYPE_WITHDRAWAL = "Вывод"
TXN_TYPES = {
    TransactionType.REPLENISHMENT: TXN_TYPE_REPLENISHMENT,
    TransactionType.WITHDRAWAL: TXN_TYPE_WITHDRAWAL,
}
