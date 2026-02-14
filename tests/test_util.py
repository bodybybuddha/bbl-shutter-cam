"""Unit tests for util.py module.

Tests logging, path utilities, and helper functions.
"""
import tempfile
from io import StringIO
from pathlib import Path

import pytest

from bbl_shutter_cam.util import (
    LogLevel,
    Logger,
    configure_logging,
    expand_path,
)


class TestLogLevel:
    """Test LogLevel enum."""

    def test_has_expected_values(self):
        """Should define standard logging levels with correct numeric values."""
        assert LogLevel.DEBUG == 10
        assert LogLevel.INFO == 20
        assert LogLevel.WARNING == 30
        assert LogLevel.ERROR == 40

    def test_ordering(self):
        """Should support numeric comparisons."""
        assert LogLevel.DEBUG < LogLevel.INFO
        assert LogLevel.INFO < LogLevel.WARNING
        assert LogLevel.WARNING < LogLevel.ERROR

    def test_enum_members(self):
        """Should have exactly 4 members."""
        assert len(list(LogLevel)) == 4


class TestLogger:
    """Test Logger class."""

    def test_default_initialization(self):
        """Should initialize with sensible defaults."""
        logger = Logger()

        assert logger.level == LogLevel.INFO
        assert logger.fmt == "plain"
        assert logger.file is None

    def test_info_logs_at_info_level(self, capsys):
        """Should log info messages when level is INFO."""
        logger = Logger(level=LogLevel.INFO, fmt="plain")

        logger.info("Test message")

        captured = capsys.readouterr()
        assert "[=] Test message" in captured.out

    def test_debug_suppressed_at_info_level(self, capsys):
        """Should not log debug messages when level is INFO."""
        logger = Logger(level=LogLevel.INFO, fmt="plain")

        logger.debug("Debug message")

        captured = capsys.readouterr()
        assert "Debug message" not in captured.out

    def test_debug_shown_at_debug_level(self, capsys):
        """Should log debug messages when level is DEBUG."""
        logger = Logger(level=LogLevel.DEBUG, fmt="plain")

        logger.debug("Debug message")

        captured = capsys.readouterr()
        assert "[D] Debug message" in captured.out

    def test_warning_logs_at_info_level(self, capsys):
        """Should log warnings even when level is INFO."""
        logger = Logger(level=LogLevel.INFO, fmt="plain")

        logger.warning("Warning message")

        captured = capsys.readouterr()
        assert "[!] Warning message" in captured.out

    def test_error_logs_at_info_level(self, capsys):
        """Should log errors even when level is INFO."""
        logger = Logger(level=LogLevel.INFO, fmt="plain")

        logger.error("Error message")

        captured = capsys.readouterr()
        assert "[X] Error message" in captured.out

    def test_plain_format_no_timestamp(self, capsys):
        """Plain format should not include timestamps."""
        logger = Logger(level=LogLevel.INFO, fmt="plain")

        logger.info("Test")

        captured = capsys.readouterr()
        assert captured.out.strip() == "[=] Test"

    def test_time_format_includes_timestamp(self, capsys):
        """Time format should include timestamp prefix."""
        logger = Logger(level=LogLevel.INFO, fmt="time")

        logger.info("Test")

        captured = capsys.readouterr()
        # Should match pattern: "YYYY-MM-DD HH:MM:SS [=] Test"
        assert "[=] Test" in captured.out
        assert len(captured.out.split()) >= 3  # Date, time, tag, message

    def test_file_output(self, tmp_path):
        """Should write to file when file handle provided."""
        log_file = tmp_path / "test.log"
        with open(log_file, "w") as f:
            logger = Logger(level=LogLevel.INFO, fmt="plain", file=f)
            logger.info("File message")

        content = log_file.read_text()
        assert "[=] File message" in content

    def test_file_output_with_stringio(self):
        """Should write to StringIO file-like object."""
        output = StringIO()
        logger = Logger(level=LogLevel.INFO, fmt="plain", file=output)

        logger.info("Test message")

        output.seek(0)
        content = output.read()
        assert "[=] Test message" in content

    def test_error_level_suppresses_lower_levels(self, capsys):
        """ERROR level should only show error messages."""
        logger = Logger(level=LogLevel.ERROR, fmt="plain")

        logger.debug("Debug")
        logger.info("Info")
        logger.warning("Warning")
        logger.error("Error")

        captured = capsys.readouterr()
        assert "Debug" not in captured.out
        assert "Info" not in captured.out
        assert "Warning" not in captured.out
        assert "Error" in captured.out

    def test_all_logs_shown_at_debug_level(self, capsys):
        """DEBUG level should show all message types."""
        logger = Logger(level=LogLevel.DEBUG, fmt="plain")

        logger.debug("Debug")
        logger.info("Info")
        logger.warning("Warning")
        logger.error("Error")

        captured = capsys.readouterr()
        assert "Debug" in captured.out
        assert "Info" in captured.out
        assert "Warning" in captured.out
        assert "Error" in captured.out

    def test_file_write_exception_handling(self):
        """Should handle file write errors gracefully."""
        # Create a closed file to trigger write error
        output = StringIO()
        output.close()

        logger = Logger(level=LogLevel.INFO, fmt="plain", file=output)

        # Should not raise exception
        logger.info("Test message")


class TestConfigureLogging:
    """Test configure_logging() function."""

    def test_sets_debug_level(self):
        """Should configure logger to DEBUG level."""
        configure_logging(level="debug", fmt="plain")

        from bbl_shutter_cam.util import LOG

        assert LOG.level == LogLevel.DEBUG

    def test_sets_info_level(self):
        """Should configure logger to INFO level."""
        configure_logging(level="info", fmt="plain")

        from bbl_shutter_cam.util import LOG

        assert LOG.level == LogLevel.INFO

    def test_sets_warning_level(self):
        """Should configure logger to WARNING level."""
        configure_logging(level="warning", fmt="plain")

        from bbl_shutter_cam.util import LOG

        assert LOG.level == LogLevel.WARNING

    def test_accepts_warn_as_alias(self):
        """Should accept 'warn' as alias for WARNING level."""
        configure_logging(level="warn", fmt="plain")

        from bbl_shutter_cam.util import LOG

        assert LOG.level == LogLevel.WARNING

    def test_sets_error_level(self):
        """Should configure logger to ERROR level."""
        configure_logging(level="error", fmt="plain")

        from bbl_shutter_cam.util import LOG

        assert LOG.level == LogLevel.ERROR

    def test_case_insensitive(self):
        """Should handle uppercase and mixed case."""
        configure_logging(level="DEBUG", fmt="plain")

        from bbl_shutter_cam.util import LOG

        assert LOG.level == LogLevel.DEBUG

    def test_raises_on_invalid_level(self):
        """Should raise ValueError for unrecognized levels."""
        with pytest.raises(ValueError, match="Invalid log level"):
            configure_logging(level="invalid", fmt="plain")

    def test_sets_plain_format(self):
        """Should set format to plain."""
        configure_logging(level="info", fmt="plain")

        from bbl_shutter_cam.util import LOG

        assert LOG.fmt == "plain"

    def test_sets_time_format(self):
        """Should set format to time."""
        configure_logging(level="info", fmt="time")

        from bbl_shutter_cam.util import LOG

        assert LOG.fmt == "time"

    def test_raises_on_invalid_format(self):
        """Should raise ValueError for invalid format."""
        with pytest.raises(ValueError, match="Invalid log format"):
            configure_logging(level="info", fmt="invalid")

    def test_creates_log_file(self, tmp_path):
        """Should create and open log file."""
        log_file = tmp_path / "test.log"

        configure_logging(level="info", fmt="plain", log_file=str(log_file))

        assert log_file.exists()

    def test_creates_log_file_parent_dirs(self, tmp_path):
        """Should create parent directories for log file."""
        log_file = tmp_path / "logs" / "app" / "test.log"

        configure_logging(level="info", fmt="plain", log_file=str(log_file))

        assert log_file.parent.exists()
        assert log_file.exists()


class TestExpandPath:
    """Test expand_path() function."""

    def test_expands_tilde(self):
        """Should expand ~ to user's home directory."""
        result = expand_path("~/test")

        assert "~" not in str(result)
        assert result.is_absolute()

    def test_expands_environment_variables(self, monkeypatch):
        """Should expand environment variables like $HOME."""
        monkeypatch.setenv("TEST_VAR", "/test/path")

        result = expand_path("$TEST_VAR/file.txt")

        assert "/test/path/file.txt" in str(result)

    def test_returns_absolute_path(self):
        """Should return absolute Path object."""
        result = expand_path("./relative/path")

        assert result.is_absolute()

    def test_handles_already_absolute_path(self):
        """Should handle already absolute paths."""
        result = expand_path("/absolute/path")

        assert result == Path("/absolute/path")

    def test_returns_pathlib_path(self):
        """Should return Path object, not string."""
        result = expand_path("~/test")

        assert isinstance(result, Path)
