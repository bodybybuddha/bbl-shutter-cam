"""Unit tests for tune.py module."""
import subprocess
from pathlib import Path

import pytest
from tomlkit import document, dumps

from bbl_shutter_cam import tune
from bbl_shutter_cam.config import load_config


def _write_minimal_config(path: Path, profile_name: str, output_dir: Path) -> None:
    cfg = document()
    cfg["default_profile"] = profile_name
    cfg["profiles"] = document()
    cfg["profiles"][profile_name] = {
        "device": {"name": "BBL_SHUTTER"},
        "camera": {
            "output_dir": str(output_dir),
            "rpicam": {
                "width": 1920,
                "height": 1080,
            },
        },
    }
    path.write_text(dumps(cfg))


def test_tuning_session_creates_test_dir(tmp_path):
    config_path = tmp_path / "config.toml"
    output_dir = tmp_path / "captures"
    _write_minimal_config(config_path, "office", output_dir)

    session = tune.TuningSession(config_path, "office")

    assert session.test_dir.exists()
    assert session.test_dir.name == "tune"


def test_tuning_session_save_to_profile(tmp_path):
    config_path = tmp_path / "config.toml"
    output_dir = tmp_path / "captures"
    _write_minimal_config(config_path, "office", output_dir)

    session = tune.TuningSession(config_path, "office")
    session.update_setting(rotation=90, quality=85, metering="spot")
    session.save_to_profile()

    updated = load_config(config_path)
    rpicam = updated["profiles"]["office"]["camera"]["rpicam"]
    assert rpicam["rotation"] == 90
    assert rpicam["quality"] == 85
    assert rpicam["metering"] == "spot"


def test_take_test_photo_success(monkeypatch, tmp_path):
    config_path = tmp_path / "config.toml"
    output_dir = tmp_path / "captures"
    _write_minimal_config(config_path, "office", output_dir)

    session = tune.TuningSession(config_path, "office")

    called = {}

    def fake_run(cmd, check=True, capture_output=True):
        called["cmd"] = cmd
        return None

    monkeypatch.setattr(tune.subprocess, "run", fake_run)

    outfile = session.take_test_photo()

    assert outfile is not None
    assert called["cmd"][0] == "rpicam-still"


def test_take_test_photo_failure(monkeypatch, tmp_path):
    config_path = tmp_path / "config.toml"
    output_dir = tmp_path / "captures"
    _write_minimal_config(config_path, "office", output_dir)

    session = tune.TuningSession(config_path, "office")

    def fake_run(*_args, **_kwargs):
        raise subprocess.CalledProcessError(1, ["rpicam-still"], stderr=b"fail")

    monkeypatch.setattr(tune.subprocess, "run", fake_run)

    outfile = session.take_test_photo()

    assert outfile is None


def test_handle_rotation_valid(monkeypatch, tmp_path):
    config_path = tmp_path / "config.toml"
    output_dir = tmp_path / "captures"
    _write_minimal_config(config_path, "office", output_dir)

    session = tune.TuningSession(config_path, "office")

    inputs = iter(["90"])
    monkeypatch.setattr("builtins.input", lambda _="": next(inputs))

    tune.handle_rotation(session)

    assert session.cam_config.rotation == 90


def test_handle_quality_out_of_range(monkeypatch, tmp_path):
    config_path = tmp_path / "config.toml"
    output_dir = tmp_path / "captures"
    _write_minimal_config(config_path, "office", output_dir)

    session = tune.TuningSession(config_path, "office")

    inputs = iter(["101"])
    monkeypatch.setattr("builtins.input", lambda _="": next(inputs))

    tune.handle_quality(session)

    assert session.cam_config.quality is None


def test_handle_multiple_settings_valid(monkeypatch, tmp_path):
    config_path = tmp_path / "config.toml"
    output_dir = tmp_path / "captures"
    _write_minimal_config(config_path, "office", output_dir)

    session = tune.TuningSession(config_path, "office")

    inputs = iter([
        "2",        # autofocus_mode -> manual
        "8.5",      # lens_position
        "1",        # ev
        "2",        # awb -> daylight
        "1.5",      # saturation
        "1.2",      # contrast
        "0.1",      # brightness
        "1.3",      # sharpness
        "3",        # denoise -> cdn_fast
        "2",        # metering -> spot
        "90",       # quality
        "10000",    # shutter
        "2.5",      # gain
    ])
    monkeypatch.setattr("builtins.input", lambda _="": next(inputs))

    tune.handle_autofocus_mode(session)
    tune.handle_lens_position(session)
    tune.handle_ev(session)
    tune.handle_awb(session)
    tune.handle_saturation(session)
    tune.handle_contrast(session)
    tune.handle_brightness(session)
    tune.handle_sharpness(session)
    tune.handle_denoise(session)
    tune.handle_metering(session)
    tune.handle_quality(session)
    tune.handle_shutter(session)
    tune.handle_gain(session)

    assert session.cam_config.autofocus_mode == "manual"
    assert session.cam_config.lens_position == 8.5
    assert session.cam_config.ev == 1
    assert session.cam_config.awb == "daylight"
    assert session.cam_config.saturation == 1.5
    assert session.cam_config.contrast == 1.2
    assert session.cam_config.brightness == 0.1
    assert session.cam_config.sharpness == 1.3
    assert session.cam_config.denoise == "cdn_fast"
    assert session.cam_config.metering == "spot"
    assert session.cam_config.quality == 90
    assert session.cam_config.shutter == 10000
    assert session.cam_config.gain == 2.5


def test_run_tuning_menu_exit(monkeypatch, tmp_path):
    config_path = tmp_path / "config.toml"
    output_dir = tmp_path / "captures"
    _write_minimal_config(config_path, "office", output_dir)

    session = tune.TuningSession(config_path, "office")

    inputs = iter(["x"])
    monkeypatch.setattr("builtins.input", lambda _="": next(inputs))
    monkeypatch.setattr(session, "show_current_settings", lambda: None)

    tune.run_tuning_menu(session)


def test_rollback_restores_original(tmp_path):
    config_path = tmp_path / "config.toml"
    output_dir = tmp_path / "captures"
    _write_minimal_config(config_path, "office", output_dir)

    session = tune.TuningSession(config_path, "office")
    original = session.cam_config

    session.update_setting(rotation=90)
    assert session.cam_config.rotation == 90

    session.rollback()
    assert session.cam_config == original


def test_show_current_settings_output(capsys, tmp_path):
    config_path = tmp_path / "config.toml"
    output_dir = tmp_path / "captures"
    _write_minimal_config(config_path, "office", output_dir)

    session = tune.TuningSession(config_path, "office")
    session.show_current_settings()

    out = capsys.readouterr().out
    assert "Camera Settings" in out
    assert "office" in out


def test_handle_save_and_exit_failure(monkeypatch, tmp_path, capsys):
    config_path = tmp_path / "config.toml"
    output_dir = tmp_path / "captures"
    _write_minimal_config(config_path, "office", output_dir)

    session = tune.TuningSession(config_path, "office")

    def fake_save():
        raise RuntimeError("save failed")

    monkeypatch.setattr(session, "save_to_profile", fake_save)

    tune.handle_save_and_exit(session)

    out = capsys.readouterr().out
    assert "Save failed" in out


def test_tune_profile_success(monkeypatch, tmp_path):
    config_path = tmp_path / "config.toml"
    output_dir = tmp_path / "captures"
    _write_minimal_config(config_path, "office", output_dir)

    monkeypatch.setattr(tune, "run_tuning_menu", lambda _session: None)
    monkeypatch.setattr("builtins.input", lambda _="": "")

    rc = tune.tune_profile(config_path, "office")

    assert rc == 0
