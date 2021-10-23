from flask import redirect
from flask import url_for

from myfunds.web import auth
from myfunds.web.views.dashboard.views import bp


@bp.route("/")
@auth.login_required
def index():
    return redirect(url_for("dashboard.joint_limits"))
