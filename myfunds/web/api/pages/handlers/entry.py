import flask

from myfunds.web.tools import auth


def login():
    if auth.is_authorized():
        redirect_url = flask.session.get("last_page", flask.url_for(".index"))
        return flask.redirect(redirect_url)
    return flask.render_template("pages/entry/login.html")


def new_account():
    if auth.is_authorized():
        redirect_url = flask.session.get("last_page", flask.url_for(".index"))
        return flask.redirect(redirect_url)
    return flask.render_template("pages/entry/new-account.html")


@auth.login_required
def index():
    return flask.redirect(flask.url_for(".balances"))
