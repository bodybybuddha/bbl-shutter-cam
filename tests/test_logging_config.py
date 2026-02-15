"""Unit tests for logging_config.py module."""

import logging
from pathlib import Path

from bbl_shutter_cam import logging_config


def test_setup_logging_with_color():
    logger = logging_config.setup_logging(level="INFO", use_color=True)

    assert logger.name == "bbl_shutter_cam"
    assert any(isinstance(h.formatter, logging_config.ColorFormatter) for h in logger.handlers)


def test_color_formatter_formats_record():
    formatter = logging_config.ColorFormatter("%(levelname)s | %(message)s")
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="hello",
        args=(),
        exc_info=None,
    )

    formatted = formatter.format(record)

    assert "hello" in formatted
    assert "INFO" in formatted


def test_setup_logging_without_color():
    logger = logging_config.setup_logging(level="INFO", use_color=False)

    assert logger.name == "bbl_shutter_cam"
    assert any(isinstance(h.formatter, logging.Formatter) for h in logger.handlers)


def test_setup_logging_with_file(tmp_path):
    log_file = tmp_path / "app.log"

    logger = logging_config.setup_logging(level="INFO", log_file=str(log_file), use_color=False)
    logger.info("test")

    assert log_file.exists()


def test_get_logger():
    logger = logging_config.get_logger("test.module")

    assert logger.name == "test.module"
