"""Unit tests for config.py module.

Tests configuration file loading, profile management, and TOML parsing.
"""
import tempfile
from pathlib import Path

import pytest
from tomlkit import document, dumps

from bbl_shutter_cam.config import (
    APP_NAME,
    ensure_config_exists,
    get_event_trigger_bytes,
    get_trigger_events,
    load_config,
    load_profile,
    save_config,
)


class TestEnsureConfigExists:
    """Test ensure_config_exists() function."""

    def test_creates_config_file_if_missing(self, tmp_path):
        """Should create config.toml with defaults when file doesn't exist."""
        config_path = tmp_path / "config.toml"
        assert not config_path.exists()

        ensure_config_exists(config_path)

        assert config_path.exists()
        assert config_path.is_file()

    def test_creates_parent_directories(self, tmp_path):
        """Should create parent directories if they don't exist."""
        config_path = tmp_path / "nested" / "dirs" / "config.toml"
        assert not config_path.parent.exists()

        ensure_config_exists(config_path)

        assert config_path.parent.exists()
        assert config_path.exists()

    def test_does_not_overwrite_existing_config(self, tmp_path):
        """Should not overwrite existing config file."""
        config_path = tmp_path / "config.toml"
        original_content = "existing = true"
        config_path.write_text(original_content)

        ensure_config_exists(config_path)

        assert config_path.read_text() == original_content

    def test_default_config_structure(self, tmp_path):
        """Should create config with expected default structure."""
        config_path = tmp_path / "config.toml"
        ensure_config_exists(config_path)

        cfg = load_config(config_path)

        assert "default_profile" in cfg
        assert cfg["default_profile"] == "default"
        assert "profiles" in cfg
        assert "default" in cfg["profiles"]
        assert "device" in cfg["profiles"]["default"]
        assert "camera" in cfg["profiles"]["default"]

    def test_default_profile_settings(self, tmp_path):
        """Should create default profile with sensible camera settings."""
        config_path = tmp_path / "config.toml"
        ensure_config_exists(config_path)

        cfg = load_config(config_path)
        default_prof = cfg["profiles"]["default"]

        assert "camera" in default_prof
        assert "rpicam" in default_prof["camera"]
        assert default_prof["camera"]["rpicam"]["width"] == 1920
        assert default_prof["camera"]["rpicam"]["height"] == 1080
        assert default_prof["camera"]["rpicam"]["nopreview"] is True


class TestLoadConfig:
    """Test load_config() function."""

    def test_loads_valid_toml(self, tmp_path):
        """Should successfully parse valid TOML configuration."""
        config_path = tmp_path / "config.toml"
        cfg_dict = document()
        cfg_dict["test_key"] = "test_value"
        config_path.write_text(dumps(cfg_dict))

        result = load_config(config_path)

        assert result["test_key"] == "test_value"

    def test_raises_on_missing_file(self, tmp_path):
        """Should raise FileNotFoundError if config doesn't exist."""
        config_path = tmp_path / "nonexistent.toml"

        with pytest.raises(FileNotFoundError):
            load_config(config_path)

    def test_loads_complex_structure(self, tmp_path):
        """Should handle nested TOML structures."""
        config_path = tmp_path / "config.toml"
        cfg = document()
        cfg["profiles"] = document()
        cfg["profiles"]["office"] = {"device": {"mac": "AA:BB:CC:DD:EE:FF"}}
        config_path.write_text(dumps(cfg))

        result = load_config(config_path)

        assert result["profiles"]["office"]["device"]["mac"] == "AA:BB:CC:DD:EE:FF"


class TestSaveConfig:
    """Test save_config() function."""

    def test_saves_config_to_file(self, tmp_path):
        """Should write configuration to specified path."""
        config_path = tmp_path / "config.toml"
        cfg = {"test": "value"}

        save_config(cfg, config_path)

        assert config_path.exists()
        loaded = load_config(config_path)
        assert loaded["test"] == "value"

    def test_creates_parent_directories(self, tmp_path):
        """Should create parent directories when saving."""
        config_path = tmp_path / "new" / "path" / "config.toml"

        save_config({"data": "value"}, config_path)

        assert config_path.parent.exists()
        assert config_path.exists()

    def test_overwrites_existing_file(self, tmp_path):
        """Should overwrite existing config file."""
        config_path = tmp_path / "config.toml"
        config_path.write_text("old = true")

        save_config({"new": "data"}, config_path)

        loaded = load_config(config_path)
        assert "new" in loaded
        assert "old" not in loaded


class TestLoadProfile:
    """Test load_profile() function."""

    def test_loads_named_profile(self, tmp_path):
        """Should load specified profile by name."""
        config_path = tmp_path / "config.toml"
        cfg = document()
        cfg["profiles"] = document()
        cfg["profiles"]["office"] = {"device": {"mac": "AA:BB:CC:DD:EE:FF"}}
        config_path.write_text(dumps(cfg))

        prof = load_profile(config_path, "office")

        assert prof["device"]["mac"] == "AA:BB:CC:DD:EE:FF"
        assert prof["_profile_name"] == "office"

    def test_loads_default_profile_when_none_specified(self, tmp_path):
        """Should load default_profile when profile_name is None."""
        config_path = tmp_path / "config.toml"
        cfg = document()
        cfg["default_profile"] = "workshop"
        cfg["profiles"] = document()
        cfg["profiles"]["workshop"] = {"device": {"name": "MY_DEVICE"}}
        config_path.write_text(dumps(cfg))

        prof = load_profile(config_path, None)

        assert prof["device"]["name"] == "MY_DEVICE"
        assert prof["_profile_name"] == "workshop"

    def test_normalizes_missing_sections(self, tmp_path):
        """Should add missing device/camera sections."""
        config_path = tmp_path / "config.toml"
        cfg = document()
        cfg["profiles"] = document()
        cfg["profiles"]["minimal"] = {}
        config_path.write_text(dumps(cfg))

        prof = load_profile(config_path, "minimal")

        assert "device" in prof
        assert "camera" in prof
        assert "rpicam" in prof["camera"]

    def test_raises_on_missing_profiles_section(self, tmp_path):
        """Should raise KeyError if [profiles] section missing."""
        config_path = tmp_path / "config.toml"
        config_path.write_text("default_profile = 'test'")

        with pytest.raises(KeyError, match="No \\[profiles\\] section"):
            load_profile(config_path, "office")

    def test_raises_on_missing_profile(self, tmp_path):
        """Should raise KeyError if requested profile doesn't exist."""
        config_path = tmp_path / "config.toml"
        cfg = document()
        cfg["profiles"] = document()
        cfg["profiles"]["office"] = {}
        config_path.write_text(dumps(cfg))

        with pytest.raises(KeyError, match="Profile 'nonexistent' not found"):
            load_profile(config_path, "nonexistent")

    def test_raises_on_missing_default_profile(self, tmp_path):
        """Should raise KeyError if profile_name is None and no default_profile set."""
        config_path = tmp_path / "config.toml"
        cfg = document()
        cfg["profiles"] = document()
        cfg["profiles"]["office"] = {}
        config_path.write_text(dumps(cfg))

        with pytest.raises(KeyError, match="No profile specified and no default_profile"):
            load_profile(config_path, None)


class TestGetTriggerEvents:
    """Test get_trigger_events() function."""

    def test_returns_configured_events(self):
        """Should return events from profile configuration."""
        profile = {
            "device": {
                "events": [
                    {
                        "uuid": "00002a4d-0000-1000-8000-00805f9b34fb",
                        "hex": "4000",
                        "capture": True,
                    },
                    {
                        "uuid": "00002a4d-0000-1000-8000-00805f9b34fb",
                        "hex": "0000",
                        "capture": False,
                    },
                ]
            }
        }

        events = get_trigger_events(profile)

        assert len(events) == 2
        assert events[0]["hex"] == "4000"
        assert events[0]["capture"] is True
        assert events[1]["hex"] == "0000"
        assert events[1]["capture"] is False

    def test_returns_defaults_when_no_events_configured(self):
        """Should return hardware defaults if no events in config."""
        profile = {"device": {}}

        events = get_trigger_events(profile)

        assert len(events) == 3
        # Should have default manual press, Bambu Studio trigger, and release event
        hex_values = [e["hex"] for e in events]
        assert "4000" in hex_values
        assert "8000" in hex_values
        assert "0000" in hex_values

    def test_all_default_events_have_capture_true(self):
        """Default capture events should have capture=True."""
        profile = {"device": {}}

        events = get_trigger_events(profile)

        # Filter to only capture events
        capture_events = [e for e in events if e.get("capture", False)]
        assert len(capture_events) == 2  # manual_button and bambu_studio
        for event in capture_events:
            assert event["capture"] is True


class TestGetEventTriggerBytes:
    """Test get_event_trigger_bytes() function."""

    def test_returns_only_capture_enabled_events(self):
        """Should filter to only events with capture=True."""
        profile = {
            "device": {
                "events": [
                    {"hex": "4000", "capture": True},
                    {"hex": "0000", "capture": False},
                    {"hex": "8000", "capture": True},
                ]
            }
        }

        result = get_event_trigger_bytes(profile)

        assert len(result) == 2
        assert b"\x40\x00" in result
        assert b"\x80\x00" in result
        assert b"\x00\x00" not in result

    def test_converts_hex_to_bytes(self):
        """Should correctly convert hex strings to bytes."""
        profile = {"device": {"events": [{"hex": "abcd", "capture": True}]}}

        result = get_event_trigger_bytes(profile)

        assert result == [b"\xab\xcd"]

    def test_returns_empty_list_when_no_capture_events(self):
        """Should return empty list if no events have capture=True."""
        profile = {
            "device": {
                "events": [
                    {"hex": "4000", "capture": False},
                    {"hex": "0000", "capture": False},
                ]
            }
        }

        result = get_event_trigger_bytes(profile)

        assert result == []

    def test_handles_empty_events_list(self):
        """Should return default triggers when no events configured."""
        profile = {"device": {}}

        result = get_event_trigger_bytes(profile)

        # Should have defaults (manual_button and bambu_studio)
        assert len(result) == 2
        assert b"\x40\x00" in result  # 4000
        assert b"\x80\x00" in result  # 8000

    def test_skips_invalid_hex_values(self):
        """Should skip events with invalid hex strings."""
        profile = {
            "device": {
                "events": [
                    {"hex": "4000", "capture": True},
                    {"hex": "invalid", "capture": True},
                    {"hex": "8000", "capture": True},
                ]
            }
        }

        result = get_event_trigger_bytes(profile)

        # Should only have the valid hex values
        assert len(result) == 2
        assert b"\x40\x00" in result
        assert b"\x80\x00" in result
