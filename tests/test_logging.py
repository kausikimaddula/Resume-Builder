"""Unit tests for centralized logging functionality."""

from __future__ import annotations

import logging
import tempfile
import unittest
from pathlib import Path

from flask import Flask

from logging_config import setup_logging


class TestLoggingConfig(unittest.TestCase):
    """Test suite for centralized logging setup and file outputs."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.log_folder = Path(self.temp_dir.name)

        self.app = Flask("test_app")
        self.app.config["LOG_LEVEL"] = "INFO"
        self.app.config["LOG_FOLDER"] = str(self.log_folder)

        setup_logging(self.app)

    def tearDown(self) -> None:
        # Close file handlers before cleanup
        for h in list(self.app.logger.handlers):
            h.close()
            self.app.logger.removeHandler(h)
        root_logger = logging.getLogger()
        for h in list(root_logger.handlers):
            h.close()
            root_logger.removeHandler(h)
        self.temp_dir.cleanup()

    def test_log_files_created(self) -> None:
        """Verify that app.log and error.log are created when logging messages occur."""
        self.app.logger.info("Test info message")
        self.app.logger.error("Test error message")

        app_log = self.log_folder / "app.log"
        error_log = self.log_folder / "error.log"

        self.assertTrue(app_log.exists(), "app.log file should be created.")
        self.assertTrue(error_log.exists(), "error.log file should be created.")

        app_log_content = app_log.read_text(encoding="utf-8")
        error_log_content = error_log.read_text(encoding="utf-8")

        self.assertIn("Test info message", app_log_content)
        self.assertIn("Test error message", app_log_content)

        # error.log should contain ERROR logs but NOT INFO logs
        self.assertIn("Test error message", error_log_content)
        self.assertNotIn("Test info message", error_log_content)


if __name__ == "__main__":
    unittest.main()
