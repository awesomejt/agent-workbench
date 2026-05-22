from flask import Flask, jsonify
from werkzeug.exceptions import HTTPException


def _err(code: str, message: str, status: int, details: dict | None = None):
    body: dict = {"error": {"code": code, "message": message}}
    if details:
        body["error"]["details"] = details
    return jsonify(body), status


def register_error_handlers(app: Flask) -> None:
    @app.errorhandler(400)
    def bad_request(e):
        return _err("bad_request", str(e.description), 400)

    @app.errorhandler(404)
    def not_found(e):
        return _err("not_found", str(e.description), 404)

    @app.errorhandler(409)
    def conflict(e):
        return _err("conflict", str(e.description), 409)

    @app.errorhandler(422)
    def unprocessable(e):
        return _err("validation_error", str(e.description), 422)

    @app.errorhandler(HTTPException)
    def http_exception(e):
        code = e.name.lower().replace(" ", "_")
        return _err(code, e.description or e.name, e.code)

    @app.errorhandler(Exception)
    def internal_error(e):
        app.logger.exception("Unhandled exception")
        return _err("internal_error", "An unexpected error occurred", 500)
