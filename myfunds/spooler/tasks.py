import uwsgi
from uwsgidecorators import timer

from myfunds.domain import models
from myfunds.tools import cmc_watchlist


@timer(30)
def update_crypto_balances_usd_price(*args):
    symbols_ids = [
        i.cmc_symbol_id
        for i in models.CryptoBalance.select(
            models.CryptoBalance.cmc_symbol_id
        ).group_by(models.CryptoBalance.cmc_symbol_id)
    ]
    ids_prices = cmc_watchlist.get_usd_price(symbols_ids)

    crypto_balances = models.CryptoBalance.select()
    for i in crypto_balances.iterator():
        price = ids_prices.get(i.cmc_symbol_id)
        if price is None:
            continue

        i.amount_usd = round(float(i.amount_repr()) * price * (10 ** 2))
        i.price = round(price * (10 ** 2))
        i.save()

    return uwsgi.SPOOL_OK
