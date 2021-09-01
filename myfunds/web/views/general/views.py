from flask import Blueprint
from flask import redirect
from flask import url_for

from myfunds.web import auth


bp = Blueprint("general", __name__, template_folder="templates")


@bp.route("/")
@auth.login_required
def index():
    return redirect(url_for("balances.index"))
