"""Logging configuration for bbl-shutter-cam.

This module provides centralized logging configuration and utilities
for different deployment scenarios (development, headless, systemd).
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional


class ColorFormatter(logging.Formatter):
    """Formatter that adds color codes for terminal output."""

    COLORS = {
        logging.DEBUG: "\033[36m",  # cyan
        logging.INFO: "\033[32m",  # green
        logging.WARNING: "\033[33m",  # yellow
        logging.ERROR: "\033[31m",  # red
        logging.CRITICAL: "\033[35m",  # magenta
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        if record.levelno in self.COLORS:
            record.levelname = f"{self.COLORS[record.levelno]}{record.levelname}{self.RESET}"
        return super().format(record)


def setup_logging(
    level: str = "INFO",
    log_file: Optional[str | Path] = None,
    use_color: bool = True,
) -> logging.Logger:
    """Configure logging for the application.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional path to log file; creates parent dirs if needed
        use_color: Whether to use colored output for terminal

    Returns:
        Configured logger instance

    Examples:
        # Development with color
        logger = setup_logging("DEBUG", use_color=True)

        # Production headless with file
        logger = setup_logging("INFO", log_file="~/.log/bbl-shutter-cam.log")

        # Both stdout and file
        setup_logging("INFO", log_file="~/.log/app.log", use_color=True)
    """
    logger = logging.getLogger("bbl_shutter_cam")
    logger.setLevel(getattr(logging, level.upper()))

    # Remove existing handlers to avoid duplicates
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, level.upper()))

    if use_color:
        formatter = ColorFormatter(fmt="%(levelname)s | %(name)s | %(message)s")
    else:
        formatter = logging.Formatter(  # type: ignore[assignment]
            fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler (if specified)
    if log_file:
        log_path = Path(log_file).expanduser()
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_path, mode="a")
        file_handler.setLevel(getattr(logging, level.upper()))

        file_formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

        logger.info("Logging to file: %s", log_path)

    return logger


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Get a logger instance for the given module name.

    Args:
        name: Module name (typically __name__). If None, returns root logger.

    Returns:
        Logger instance
    """
    return logging.getLogger(name or "bbl_shutter_cam")
