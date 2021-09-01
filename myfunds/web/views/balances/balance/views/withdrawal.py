from flask import render_template

from myfunds.web import auth
from myfunds.web.views.balances.balance.views import bp
from myfunds.web.views.balances.balance.views import verify_balance


@bp.route("/withdrawal")
@auth.login_required
@verify_balance
def withdrawal():
    return render_template("balance/withdrawal.html")
