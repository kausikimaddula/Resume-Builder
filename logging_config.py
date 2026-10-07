"""Centralized logging configuration module with MongoDB log storage."""

from __future__ import annotations

from datetime import datetime
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from flask import Flask


class ErrorOnlyFilter(logging.Filter):
    """Filter that passes only ERROR and CRITICAL level records."""

    def filter(self, record: logging.LogRecord) -> bool:
        return record.levelno >= logging.ERROR


class MongoDBHandler(logging.Handler):
    """Logging handler that persists structured log records into MongoDB."""

    def __init__(
        self,
        level: int | str = logging.NOTSET,
        mongo_uri: str | None = None,
        db_name: str | None = None,
    ) -> None:
        super().__init__(level)
        self.mongo_uri = mongo_uri
        self.db_name = db_name
        self._is_emitting = False

    def emit(self, record: logging.LogRecord) -> None:
        if self._is_emitting:
            return
        try:
            self._is_emitting = True
            from services.database import get_mongo_db

            db = get_mongo_db(self.mongo_uri, self.db_name)
            if db is None:
                return

            log_doc = {
                "timestamp": datetime.utcnow().isoformat(),
                "created": record.created,
                "level": record.levelname,
                "levelno": record.levelno,
                "logger": record.name,
                "message": record.getMessage(),
                "module": record.module,
                "func_name": record.funcName,
                "line_no": record.lineno,
            }
            if record.exc_info:
                log_doc["exception"] = self.format(record)
            db.logs.insert_one(log_doc)
        except Exception:
            self.handleError(record)
        finally:
            self._is_emitting = False


def setup_logging(app: Flask) -> None:
    """Configure centralized console, application log, error log, and MongoDB handlers.

    Args:
        app: Flask application instance.
    """
    log_level = app.config.get("LOG_LEVEL", "INFO")
    if isinstance(log_level, str):
        log_level = getattr(logging, log_level.upper(), logging.INFO)

    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] [%(name)s] %(message)s"
    )

    handlers: list[logging.Handler] = []

    # 1. MongoDB Logging Handler (Persists all structured logs into MongoDB)
    try:
        mongo_uri = app.config.get("MONGO_URI") or app.config.get("DATABASE_URL")
        mongo_db_name = app.config.get("MONGO_DB_NAME")
        mongo_handler = MongoDBHandler(
            level=log_level,
            mongo_uri=mongo_uri,
            db_name=mongo_db_name,
        )
        mongo_handler.setFormatter(formatter)
        handlers.append(mongo_handler)
    except Exception:
        pass

    # 2. File Logging Handlers (if filesystem is writable)
    try:
        log_folder = Path(app.config.get("LOG_FOLDER", Path("logs")))
        log_folder.mkdir(parents=True, exist_ok=True)

        app_log_handler = RotatingFileHandler(
            log_folder / "app.log",
            maxBytes=2_000_000,
            backupCount=5,
            encoding="utf-8",
        )
        app_log_handler.setLevel(log_level)
        app_log_handler.setFormatter(formatter)
        handlers.append(app_log_handler)

        error_log_handler = RotatingFileHandler(
            log_folder / "error.log",
            maxBytes=2_000_000,
            backupCount=5,
            encoding="utf-8",
        )
        error_log_handler.setLevel(logging.ERROR)
        error_log_handler.addFilter(ErrorOnlyFilter())
        error_log_handler.setFormatter(formatter)
        handlers.append(error_log_handler)
    except (OSError, PermissionError):
        # Read-only filesystem (e.g. Vercel serverless)
        pass

    # 3. StreamHandler for console output (always active and compatible with Vercel)
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(log_level)
    stream_handler.setFormatter(formatter)
    handlers.append(stream_handler)

    # Clear existing handlers on app logger and root logger to prevent duplicate output
    for h in list(app.logger.handlers):
        app.logger.removeHandler(h)
        h.close()

    app.logger.setLevel(log_level)
    for h in handlers:
        app.logger.addHandler(h)

    # Attach handlers to root logger so service loggers propagate
    root_logger = logging.getLogger()
    for h in list(root_logger.handlers):
        root_logger.removeHandler(h)
        h.close()

    root_logger.setLevel(log_level)
    for h in handlers:
        root_logger.addHandler(h)
