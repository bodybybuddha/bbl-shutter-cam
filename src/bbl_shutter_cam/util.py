"""Logging and utility functions.

Provides:
    - LogLevel enum: Logging severity levels
    - Logger class: Simple custom logger for consistent output
    - configure_logging(): Global logger setup
    - Path/dict utilities: expand_path, ensure_dir, safe_get, etc.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import IntEnum
from pathlib import Path
from typing import Any, Iterable, Optional, TextIO


class LogLevel(IntEnum):
    """Logging severity levels (compatible with Python logging module).
    
    Attributes:
        DEBUG: 10 - Detailed diagnostic information
        INFO: 20 - General informational messages
        WARNING: 30 - Warning messages for potentially problematic situations
        ERROR: 40 - Error messages for serious problems
    """


_LEVEL_NAMES = {
    "debug": LogLevel.DEBUG,
    "info": LogLevel.INFO,
    "warning": LogLevel.WARNING,
    "warn": LogLevel.WARNING,
    "error": LogLevel.ERROR,
}


@dataclass
class Logger:
    """Simple custom logger with optional file output and formatting.
    
    Attributes:
        level: LogLevel threshold; messages below this level are ignored
        fmt: Format style - "plain" for no timestamps, "time" to include timestamps
        file: Optional open file handle for appending log output
    
    Example:
        >>> LOG = Logger(level=LogLevel.INFO, fmt="time")
        >>> LOG.info("Starting application")
        2026-02-14 12:34:56 [=] Starting application
    """
    level: LogLevel = LogLevel.INFO
    fmt: str = "plain"  # "plain" | "time"
    file: Optional[TextIO] = None

    def _prefix(self, tag: str) -> str:
        """Generate log line prefix with optional timestamp.
        
        Args:
            tag: Short tag like '[D]', '[=]', '[!]', '[X]'
        
        Returns:
            Formatted prefix string
        """
        if self.fmt == "time":
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            return f"{ts} {tag}"
        return tag

    def _write(self, line: str) -> None:
        """Write log line to stdout and optional file.
        
        Args:
            line: Complete formatted log line
        """
        print(line)
        if self.file:
            try:
                self.file.write(line + "\n")
                self.file.flush()
            except Exception:
                pass

    def debug(self, msg: str) -> None:
        """Log a debug-level message.
        
        Args:
            msg: Message to log
        """
        if self.level <= LogLevel.DEBUG:
            self._write(f"{self._prefix('[D]')} {msg}")

    def info(self, msg: str) -> None:
        """Log an info-level message.
        
        Args:
            msg: Message to log
        """
        if self.level <= LogLevel.INFO:
            self._write(f"{self._prefix('[=]')} {msg}")

    def warning(self, msg: str) -> None:
        """Log a warning-level message.
        
        Args:
            msg: Message to log
        """
        if self.level <= LogLevel.WARNING:
            self._write(f"{self._prefix('[!]')} {msg}")

    def error(self, msg: str) -> None:
        """Log an error-level message.
        
        Args:
            msg: Message to log
        """
        if self.level <= LogLevel.ERROR:
            self._write(f"{self._prefix('[X]')} {msg}")


# Global logger instance used throughout the application.
LOG = Logger()


def configure_logging(
    level: str = "info",
    fmt: str = "plain",
    log_file: Optional[str | Path] = None,
) -> None:
    """Configure the global logger instance.
    
    Args:
        level: Log level as string: "debug", "info", "warning", "error"
        fmt: Log format - "plain" (no timestamps) or "time" (with timestamps)
        log_file: Optional file path for logging (creates parent dirs automatically)
    
    Raises:
        ValueError: If level or fmt are invalid
    
    Example:
        >>> configure_logging(level="debug", fmt="time", log_file="~/.log/app.log")
        >>> LOG.debug("This appears in both stdout and file")
    """
    lvl = _LEVEL_NAMES.get(level.lower())
    if lvl is None:
        raise ValueError(f"Invalid log level: {level!r} (use debug|info|warning|error)")
    if fmt not in ("plain", "time"):
        raise ValueError(f"Invalid log format: {fmt!r} (use plain|time)")

    LOG.level = lvl
    LOG.fmt = fmt

    if log_file:
        path = Path(log_file).expanduser()
        path.parent.mkdir(parents=True, exist_ok=True)
        LOG.file = path.open("a", buffering=1)
        LOG.debug(f"Logging to file: {path}")


def expand_path(p: str | Path) -> Path:
    """Expand user home directory shortcut to absolute path.
    
    Args:
        p: Path string or Path object (may contain ~)
    
    Returns:
        Path: Absolute expanded path
    
    Example:
        >>> expand_path("~/documents")
        PosixPath('/home/user/documents')
    """
    return Path(p).expanduser()


def ensure_dir(p: str | Path) -> Path:
    """Create directory if it doesn't exist and return the path.
    
    Args:
        p: Directory path (may contain ~)
    
    Returns:
        Path: Absolute expanded path to the directory
    
    Example:
        >>> ensure_dir("~/captures/photos").mkdir() if not exists
    """
    d = expand_path(p)
    d.mkdir(parents=True, exist_ok=True)
    return d


def safe_get(d: dict, keys: Iterable[str], default: Any = None) -> Any:
    """Safely access nested dictionary keys with default fallback.
    
    Traverses a nested dict structure safely, returning default if any
    key is missing or if a non-dict value is encountered mid-traversal.
    
    Args:
        d: Dictionary to access
        keys: Sequence of keys to traverse (e.g., ["level1", "level2"])
        default: Value to return if any key is missing
    
    Returns:
        The nested value or default
    
    Example:
        >>> config = {"server": {"host": "localhost", "port": 8080}}
        >>> safe_get(config, ["server", "host"])
        'localhost'
        >>> safe_get(config, ["server", "ssl"], default=False)
        False
    """


def fmt_kv(title: str, value: Optional[Any]) -> str:
    """Format a key-value pair for display.
    
    Simple utility for consistent output formatting, treating None as empty.
    
    Args:
        title: Display label/key
        value: Value to display (or None)
    
    Returns:
        Formatted string like "Title: value"
    
    Example:
        >>> fmt_kv("Status", "Connected")
        'Status: Connected'
        >>> fmt_kv("Optional", None)
        'Optional: '
    """
