from flask import render_template

from myfunds.web import auth
from myfunds.web.views.balances.balance.views import bp
from myfunds.web.views.balances.balance.views import verify_balance


@bp.route("/statistics")
@auth.login_required
@verify_balance
def statistics():
    return render_template("balance/statistics.html")
