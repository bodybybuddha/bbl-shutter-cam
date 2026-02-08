# src/bbl_shutter_cam/util.py
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import IntEnum
from pathlib import Path
from typing import Any, Iterable, Optional, TextIO


class LogLevel(IntEnum):
    DEBUG = 10
    INFO = 20
    WARNING = 30
    ERROR = 40


_LEVEL_NAMES = {
    "debug": LogLevel.DEBUG,
    "info": LogLevel.INFO,
    "warning": LogLevel.WARNING,
    "warn": LogLevel.WARNING,
    "error": LogLevel.ERROR,
}


@dataclass
class Logger:
    level: LogLevel = LogLevel.INFO
    fmt: str = "plain"  # "plain" | "time"
    file: Optional[TextIO] = None

    def _prefix(self, tag: str) -> str:
        if self.fmt == "time":
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            return f"{ts} {tag}"
        return tag

    def _write(self, line: str) -> None:
        print(line)
        if self.file:
            try:
                self.file.write(line + "\n")
                self.file.flush()
            except Exception:
                pass

    def debug(self, msg: str) -> None:
        if self.level <= LogLevel.DEBUG:
            self._write(f"{self._prefix('[D]')} {msg}")

    def info(self, msg: str) -> None:
        if self.level <= LogLevel.INFO:
            self._write(f"{self._prefix('[=]')} {msg}")

    def warning(self, msg: str) -> None:
        if self.level <= LogLevel.WARNING:
            self._write(f"{self._prefix('[!]')} {msg}")

    def error(self, msg: str) -> None:
        if self.level <= LogLevel.ERROR:
            self._write(f"{self._prefix('[X]')} {msg}")


# Global logger
LOG = Logger()


def configure_logging(
    level: str = "info",
    fmt: str = "plain",
    log_file: Optional[str | Path] = None,
) -> None:
    """
    Configure global logger.
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
    return Path(p).expanduser()


def ensure_dir(p: str | Path) -> Path:
    d = expand_path(p)
    d.mkdir(parents=True, exist_ok=True)
    return d


def safe_get(d: dict, keys: Iterable[str], default: Any = None) -> Any:
    cur: Any = d
    for k in keys:
        if not isinstance(cur, dict) or k not in cur:
            return default
        cur = cur[k]
    return cur


def fmt_kv(title: str, value: Optional[Any]) -> str:
    return f"{title}: {value if value is not None else ''}"
