from __future__ import annotations

from flask import Flask, jsonify
from sqlalchemy import text

from .config import Settings
from .database import db
from .errors import register_error_handlers


def create_app(settings: Settings | None = None) -> Flask:
    if settings is None:
        settings = Settings()  # type: ignore[call-arg]  # pydantic-settings reads from env

    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = settings.database_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SECRET_KEY"] = settings.secret_key
    app.config["APP_ENV"] = settings.app_env
    app.config["SETTINGS"] = settings

    db.init_app(app)
    register_error_handlers(app)
    _register_blueprints(app)

    if settings.prometheus_enabled:
        from .metrics import setup_metrics

        setup_metrics(app)

    @app.get("/health")
    def health():
        try:
            db.session.execute(text("SELECT 1"))
            db_status = "ok"
        except Exception:
            db_status = "unavailable"
        status = "ok" if db_status == "ok" else "degraded"
        code = 200 if status == "ok" else 503
        return jsonify({"status": status, "env": settings.app_env, "db": db_status}), code

    return app


def _register_blueprints(app: Flask) -> None:
    from .agents.routes import bp as agents_bp
    from .ai_servers.routes import bp as ai_servers_bp
    from .events.routes import bp as events_bp
    from .project_sections.routes import bp as sections_bp
    from .project_status.routes import bp as status_bp
    from .projects.routes import bp as projects_bp
    from .reviews.routes import bp as reviews_bp
    from .runs.routes import bp as runs_bp
    from .tasks.routes import bp as tasks_bp

    app.register_blueprint(projects_bp)
    app.register_blueprint(sections_bp)
    app.register_blueprint(status_bp)
    app.register_blueprint(tasks_bp)
    app.register_blueprint(agents_bp)
    app.register_blueprint(runs_bp)
    app.register_blueprint(events_bp)
    app.register_blueprint(reviews_bp)
    app.register_blueprint(ai_servers_bp)


def main() -> None:
    settings = Settings()  # type: ignore[call-arg]  # pydantic-settings reads from env
    app = create_app(settings)
    app.run(
        host=settings.api_host,
        port=settings.api_port,
        debug=settings.app_env == "local",
    )
