from flask import g
from flask import redirect
from flask import url_for

from myfunds.web import auth
from myfunds.web.views.joint_limits.limit.views import bp
from myfunds.web.views.joint_limits.limit.views import verify_limit


@bp.route("/")
@auth.login_required
@auth.superuser_required
@verify_limit
def index():
    return redirect(url_for("joint_limits.i.participants", limit_id=g.limit.id))
