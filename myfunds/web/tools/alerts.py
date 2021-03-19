from flask import flash


def info(message: str) -> None:
    flash(message, "info")


def success(message: str) -> None:
    flash(message, "success")


def warning(message: str) -> None:
    flash(message, "warning")


def error(message: str) -> None:
    flash(message, "danger")
