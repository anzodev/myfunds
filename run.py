import os

from myfunds.web.utils import disable_werkzeug_logs
from wsgi import app


if __name__ == "__main__":
    disable_werkzeug_logs()

    # Disable Flask messages.
    os.environ["WERKZEUG_RUN_MAIN"] = "true"

    app.templates_auto_reload = True
    app.jinja_options["auto_reload"] = True

    host, port = app.config["WEB_RUN_ON_HOST"], app.config["WEB_RUN_ON_PORT"]
    print(f"Running on http://{host}:{port}/")

    app.run(host=host, port=port, use_reloader=True, threaded=True)
