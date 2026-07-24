"""Centralized logging configuration module."""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from flask import Flask


class ErrorOnlyFilter(logging.Filter):
    """Filter that passes only ERROR and CRITICAL level records."""

    def filter(self, record: logging.LogRecord) -> bool:
        return record.levelno >= logging.ERROR


def setup_logging(app: Flask) -> None:
    """Configure centralized console, application log, and error log handlers.

    Args:
        app: Flask application instance.
    """
    log_level = app.config.get("LOG_LEVEL", "INFO")
    if isinstance(log_level, str):
        log_level = getattr(logging, log_level.upper(), logging.INFO)

    log_folder = Path(app.config.get("LOG_FOLDER", Path("logs")))
    log_folder.mkdir(parents=True, exist_ok=True)

    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] [%(name)s] %(message)s"
    )

    # 1. RotatingFileHandler for general app log (logs everything at log_level)
    app_log_handler = RotatingFileHandler(
        log_folder / "app.log",
        maxBytes=2_000_000,
        backupCount=5,
        encoding="utf-8",
    )
    app_log_handler.setLevel(log_level)
    app_log_handler.setFormatter(formatter)

    # 2. Dedicated RotatingFileHandler for error logs (ERROR and CRITICAL only)
    error_log_handler = RotatingFileHandler(
        log_folder / "error.log",
        maxBytes=2_000_000,
        backupCount=5,
        encoding="utf-8",
    )
    error_log_handler.setLevel(logging.ERROR)
    error_log_handler.addFilter(ErrorOnlyFilter())
    error_log_handler.setFormatter(formatter)

    # 3. StreamHandler for console output
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(log_level)
    stream_handler.setFormatter(formatter)

    # Clear existing handlers on app logger and root logger to prevent duplicate output
    for h in list(app.logger.handlers):
        app.logger.removeHandler(h)
        h.close()

    app.logger.setLevel(log_level)
    app.logger.addHandler(app_log_handler)
    app.logger.addHandler(error_log_handler)
    app.logger.addHandler(stream_handler)

    # Attach handlers to root logger so service loggers (e.g. logging.getLogger("services.openai_service")) propagate
    root_logger = logging.getLogger()
    for h in list(root_logger.handlers):
        root_logger.removeHandler(h)
        h.close()

    root_logger.setLevel(log_level)
    root_logger.addHandler(app_log_handler)
    root_logger.addHandler(error_log_handler)
    root_logger.addHandler(stream_handler)
