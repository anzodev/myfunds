from wsgi import app


if __name__ == "__main__":
    app.templates_auto_reload = True
    app.jinja_options["auto_reload"] = True
    app.run(use_reloader=True, threaded=True)
