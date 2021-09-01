from flask import g
from flask import redirect
from flask import url_for

from myfunds.web import auth
from myfunds.web.views.balances.balance.views import bp
from myfunds.web.views.balances.balance.views import verify_balance


@bp.route("/")
@auth.login_required
@verify_balance
def index():
    return redirect(url_for("balances.i.transactions", balance_id=g.balance.id))
