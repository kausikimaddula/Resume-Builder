"""Application entry point for the AI Resume Builder & Tracker."""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from flask import Flask, render_template
from flask_migrate import Migrate
from werkzeug.exceptions import HTTPException

from config import Config
from models import db
from routes.main import main_bp

migrate = Migrate()


def create_app(config_class: type[Config] = Config) -> Flask:
    """Create and configure the Flask application.

    Keeping app setup in a function makes the project easier to test and grow.
    """
    app = Flask(__name__)

    # Load settings from config.py. That file reads values from environment
    # variables, so secrets do not need to be hard-coded in the app.
    app.config.from_object(config_class)

    # Ensure instance directory exists for SQLite database
    instance_dir = Path(app.root_path) / "instance"
    instance_dir.mkdir(parents=True, exist_ok=True)

    # Initialize SQLAlchemy database and Flask-Migrate
    db.init_app(app)
    migrate.init_app(app, db)

    with app.app_context():
        db.create_all()

    # Keep setup steps small and named so new developers can follow the flow.
    configure_logging(app)
    register_blueprints(app)
    register_error_handlers(app)

    app.logger.info("AI Resume Builder & Tracker started")
    return app



def configure_logging(app: Flask) -> None:
    """Configure console and file logging for the application."""
    log_level = app.config["LOG_LEVEL"]
    log_folder = Path(app.config["LOG_FOLDER"])

    # Create the logs folder automatically when the app starts.
    log_folder.mkdir(parents=True, exist_ok=True)

    formatter = logging.Formatter(
        "%(asctime)s %(levelname)s [%(name)s] %(message)s"
    )

    # RotatingFileHandler keeps log files from growing forever.
    file_handler = RotatingFileHandler(
        log_folder / "app.log",
        maxBytes=1_000_000,
        backupCount=3,
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)

    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(log_level)
    stream_handler.setFormatter(formatter)

    app.logger.handlers.clear()
    app.logger.setLevel(log_level)
    app.logger.addHandler(file_handler)
    app.logger.addHandler(stream_handler)


def register_blueprints(app: Flask) -> None:
    """Register route groups for the app."""
    # Blueprints let the project grow without putting every route in app.py.
    app.register_blueprint(main_bp)


def register_error_handlers(app: Flask) -> None:
    """Render simple user-friendly pages for common application errors."""

    @app.errorhandler(HTTPException)
    def handle_http_exception(error: HTTPException):
        app.logger.warning("HTTP error %s: %s", error.code, error.description)
        return (
            render_template(
                "error.html",
                error_code=error.code,
                error_message=error.description,
            ),
            error.code,
        )

    @app.errorhandler(Exception)
    def handle_unexpected_exception(error: Exception):
        app.logger.exception("Unexpected application error: %s", error)
        return (
            render_template(
                "error.html",
                error_code=500,
                error_message="Something went wrong. Please try again soon.",
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
