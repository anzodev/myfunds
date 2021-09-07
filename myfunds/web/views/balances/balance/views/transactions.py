from flask import render_template

from myfunds.web import auth
from myfunds.web.views.balances.balance.views import bp
from myfunds.web.views.balances.balance.views import verify_balance


@bp.route("/transactions")
@auth.login_required
@verify_balance
def transactions():
    return render_template("balance/transactions.html")