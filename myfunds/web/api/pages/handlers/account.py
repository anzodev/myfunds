from flask import g
from flask import render_template

from myfunds.web.tools import auth


@auth.login_required
def edit():
    ip_whitelist_form_data = {"ip_whitelist": ";".join(g.account.ip_whitelist)}
    return render_template(
        "pages/account/edit.html", ip_whitelist_form_data=ip_whitelist_form_data
    )
