from myfunds.web.utils import disable_werkzeug_logs
from wsgi import app


if __name__ == "__main__":
    disable_werkzeug_logs()

    app.templates_auto_reload = True
    app.jinja_options["auto_reload"] = True
    app.run()
