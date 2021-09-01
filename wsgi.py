from myfunds.web import create_app
from myfunds.web.config import init_config
from myfunds.web.utils import parse_env_parser


args = parse_env_parser()
config = init_config(args.env)
app = create_app(config)


if __name__ == "__main__":
    app.templates_auto_reload = True
    app.jinja_options["auto_reload"] = True
    app.run(use_reloader=True, threaded=True)
