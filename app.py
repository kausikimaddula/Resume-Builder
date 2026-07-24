"""Application entry point for the AI Resume Builder & Tracker."""

from __future__ import annotations

import logging
from flask import Flask, flash, jsonify, redirect, render_template, request, url_for
from werkzeug.exceptions import HTTPException

from config import Config
from logging_config import setup_logging
from routes.main import main_bp
from services.exceptions import AppBaseException
from services.version_service import init_db

logger = logging.getLogger(__name__)


def create_app(config_class: type[Config] = Config) -> Flask:
    """Create and configure the Flask application.

    Keeping app setup in a function makes the project easier to test and grow.
    """
    app = Flask(__name__)

    # Load settings from config.py.
    app.config.from_object(config_class)

    # Centralized logging configuration
    setup_logging(app)
    register_blueprints(app)
    register_error_handlers(app)

    # Initialize SQLite Database for Resume Versioning
    try:
        init_db(app.config["DATABASE_PATH"])
    except Exception as exc:
        app.logger.error("Failed to initialize database on startup: %s", exc, exc_info=True)

    app.logger.info("AI Resume Builder & Tracker started")
    return app


def register_blueprints(app: Flask) -> None:
    """Register route groups for the app."""
    app.register_blueprint(main_bp)


def register_error_handlers(app: Flask) -> None:
    """Render user-friendly error pages and log detailed developer diagnostics."""

    @app.errorhandler(AppBaseException)
    def handle_app_base_exception(error: AppBaseException):
        app.logger.error(
            "Application domain error [%s]: %s (Details: %s)",
            error.__class__.__name__,
            error.message,
            error.details,
            exc_info=True,
        )

        if request.path.startswith("/api/") or request.is_json:
            return jsonify({
                "error": error.__class__.__name__,
                "message": error.user_message,
            }), error.status_code

        return (
            render_template(
                "error.html",
                error_code=error.status_code,
                error_message=error.user_message,
            ),
            error.status_code,
        )

    @app.errorhandler(HTTPException)
    def handle_http_exception(error: HTTPException):
        app.logger.warning("HTTP error %s: %s", error.code, error.description)

        if request.path.startswith("/api/") or request.is_json:
            return jsonify({
                "error": error.name,
                "message": error.description,
            }), error.code or 400

        return (
            render_template(
                "error.html",
                error_code=error.code or 400,
                error_message=error.description,
            ),
            error.code or 400,
        )

    @app.errorhandler(Exception)
    def handle_unexpected_exception(error: Exception):
        app.logger.exception("Unhandled unexpected application exception: %s", error)

        if request.path.startswith("/api/") or request.is_json:
            return jsonify({
                "error": "InternalServerError",
                "message": "An unexpected error occurred. Please try again later.",
            }), 500

        return (
            render_template(
                "error.html",
                error_code=500,
                error_message="Something went wrong on our end. Please try again soon.",
            ),
            500,
        )


app = create_app()


if __name__ == "__main__":
    app.run(
        host=app.config["HOST"],
        port=app.config["PORT"],
        debug=app.config["DEBUG"],
    )
