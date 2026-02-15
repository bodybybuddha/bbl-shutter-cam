"""Unit tests for camera.py module.

Tests camera configuration, command building, and file management.
"""

import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from bbl_shutter_cam.camera import (
    CameraConfig,
    build_rpicam_still_cmd,
    camera_config_from_profile,
    make_outfile,
)


class TestCameraConfig:
    """Test CameraConfig dataclass."""

    def test_minimal_initialization(self):
        """Should initialize with only required fields."""
        config = CameraConfig(output_dir="/tmp/captures")

        assert config.output_dir == "/tmp/captures"
        assert config.filename_format == "%Y%m%d_%H%M%S.jpg"
        assert config.min_interval_sec == 0.5
        assert config.width == 1920
        assert config.height == 1080
        assert config.nopreview is True

    def test_is_frozen(self):
        """Should be immutable (frozen dataclass)."""
        config = CameraConfig(output_dir="/tmp")

        with pytest.raises(Exception):  # FrozenInstanceError
            config.width = 3840

    def test_optional_parameters_default_to_none(self):
        """Optional camera parameters should default to None."""
        config = CameraConfig(output_dir="/tmp")

        assert config.rotation is None
        assert config.awb is None
        assert config.ev is None
        assert config.shutter is None
        assert config.saturation is None
        assert config.metering is None
        assert config.quality is None

    def test_all_optional_parameters_settable(self):
        """Should accept all optional camera parameters."""
        config = CameraConfig(
            output_dir="/tmp",
            rotation=180,
            hflip=True,
            vflip=True,
            awb="daylight",
            ev=2,
            denoise="cdn_hq",
            sharpness=1.5,
            shutter=10000,
            gain=2.0,
            awbgains="1.5,1.8",
            saturation=1.2,
            contrast=1.1,
            brightness=0.1,
            metering="spot",
            autofocus_mode="continuous",
            lens_position=5.0,
            quality=95,
            timeout=2000,
        )

        assert config.rotation == 180
        assert config.hflip is True
        assert config.saturation == 1.2
        assert config.metering == "spot"
        assert config.quality == 95


class TestCameraConfigFromProfile:
    """Test camera_config_from_profile() function."""

    def test_loads_basic_camera_settings(self):
        """Should extract camera settings from profile dict."""
        profile = {
            "_profile_name": "test",
            "camera": {
                "output_dir": "/test/output",
                "filename_format": "%H%M%S.jpg",
                "min_interval_sec": 1.0,
                "rpicam": {
                    "width": 3840,
                    "height": 2160,
                },
            },
        }

        config = camera_config_from_profile(profile)

        assert config.output_dir == "/test/output"
        assert config.filename_format == "%H%M%S.jpg"
        assert config.min_interval_sec == 1.0
        assert config.width == 3840
        assert config.height == 2160

    def test_uses_defaults_for_missing_settings(self):
        """Should apply sensible defaults when settings missing."""
        profile = {"_profile_name": "test", "camera": {}}

        config = camera_config_from_profile(profile)

        # Default output_dir should include profile name
        assert "test" in config.output_dir
        assert config.filename_format == "%Y%m%d_%H%M%S.jpg"
        assert config.min_interval_sec == 0.5

    def test_default_output_dir_includes_profile_name(self):
        """Default output_dir should be ~/captures/{profile_name}/."""
        profile = {"_profile_name": "office", "camera": {}}

        config = camera_config_from_profile(profile)

        assert "office" in config.output_dir
        assert "captures" in config.output_dir

    def test_loads_extended_camera_parameters(self):
        """Should load all extended camera parameters."""
        profile = {
            "_profile_name": "test",
            "camera": {
                "rpicam": {
                    "rotation": 90,
                    "hflip": True,
                    "vflip": False,
                    "awb": "tungsten",
                    "ev": -2,
                    "saturation": 1.3,
                    "contrast": 1.2,
                    "brightness": 0.2,
                    "metering": "spot",
                    "autofocus_mode": "manual",
                    "lens_position": 10.5,
                    "quality": 90,
                    "timeout": 5000,
                },
            },
        }

        config = camera_config_from_profile(profile)

        assert config.rotation == 90
        assert config.hflip is True
        assert config.vflip is False
        assert config.awb == "tungsten"
        assert config.ev == -2
        assert config.saturation == 1.3
        assert config.metering == "spot"
        assert config.lens_position == 10.5
        assert config.quality == 90

    def test_handles_empty_profile(self):
        """Should handle minimal profile with defaults."""
        profile = {"_profile_name": "minimal"}

        config = camera_config_from_profile(profile)

        assert isinstance(config, CameraConfig)
        assert "minimal" in config.output_dir


class TestBuildRpicamStillCmd:
    """Test build_rpicam_still_cmd() function."""

    def test_basic_command_structure(self):
        """Should build basic rpicam-still command."""
        config = CameraConfig(
            output_dir="/tmp",
            width=1920,
            height=1080,
            nopreview=True,
        )

        cmd = build_rpicam_still_cmd(config, "/tmp/test.jpg")

        assert cmd[0] == "rpicam-still"
        assert "--width" in cmd
        assert "1920" in cmd
        assert "--height" in cmd
        assert "1080" in cmd
        assert "--nopreview" in cmd
        assert "-o" in cmd
        assert "/tmp/test.jpg" in cmd

    def test_includes_rotation(self):
        """Should include rotation parameter when set."""
        config = CameraConfig(output_dir="/tmp", rotation=180)

        cmd = build_rpicam_still_cmd(config, "/tmp/out.jpg")

        assert "--rotation" in cmd
        assert "180" in cmd

    def test_includes_flip_parameters(self):
        """Should include flip parameters when enabled."""
        config = CameraConfig(output_dir="/tmp", hflip=True, vflip=True)

        cmd = build_rpicam_still_cmd(config, "/tmp/out.jpg")

        assert "--hflip" in cmd
        assert "--vflip" in cmd

    def test_includes_awb_mode(self):
        """Should include AWB mode when set."""
        config = CameraConfig(output_dir="/tmp", awb="daylight")

        cmd = build_rpicam_still_cmd(config, "/tmp/out.jpg")

        assert "--awb" in cmd
        assert "daylight" in cmd

    def test_includes_exposure_compensation(self):
        """Should include EV when set."""
        config = CameraConfig(output_dir="/tmp", ev=3)

        cmd = build_rpicam_still_cmd(config, "/tmp/out.jpg")

        assert "--ev" in cmd
        assert "3" in cmd

    def test_includes_color_adjustments(self):
        """Should include saturation, contrast, brightness."""
        config = CameraConfig(
            output_dir="/tmp",
            saturation=1.5,
            contrast=1.2,
            brightness=0.3,
        )

        cmd = build_rpicam_still_cmd(config, "/tmp/out.jpg")

        assert "--saturation" in cmd
        assert "1.5" in cmd
        assert "--contrast" in cmd
        assert "1.2" in cmd
        assert "--brightness" in cmd
        assert "0.3" in cmd

    def test_includes_metering_mode(self):
        """Should include metering mode when set."""
        config = CameraConfig(output_dir="/tmp", metering="spot")

        cmd = build_rpicam_still_cmd(config, "/tmp/out.jpg")

        assert "--metering" in cmd
        assert "spot" in cmd

    def test_includes_autofocus_settings(self):
        """Should include autofocus mode and lens position."""
        config = CameraConfig(
            output_dir="/tmp",
            autofocus_mode="manual",
            lens_position=8.5,
        )

        cmd = build_rpicam_still_cmd(config, "/tmp/out.jpg")

        assert "--autofocus-mode" in cmd
        assert "manual" in cmd
        assert "--lens-position" in cmd
        assert "8.5" in cmd

    def test_includes_quality(self):
        """Should include JPEG quality when set."""
        config = CameraConfig(output_dir="/tmp", quality=85)

        cmd = build_rpicam_still_cmd(config, "/tmp/out.jpg")

        assert "--quality" in cmd
        assert "85" in cmd

    def test_includes_timeout(self):
        """Should include timeout when set."""
        config = CameraConfig(output_dir="/tmp", timeout=3000)

        cmd = build_rpicam_still_cmd(config, "/tmp/out.jpg")

        assert "--timeout" in cmd
        assert "3000" in cmd

    def test_omits_none_values(self):
        """Should not include parameters set to None."""
        config = CameraConfig(
            output_dir="/tmp",
            rotation=None,
            awb=None,
            saturation=None,
        )

        cmd = build_rpicam_still_cmd(config, "/tmp/out.jpg")

        assert "--rotation" not in cmd
        assert "--awb" not in cmd
        assert "--saturation" not in cmd

    def test_command_is_list_of_strings(self):
        """Should return list of strings suitable for subprocess."""
        config = CameraConfig(output_dir="/tmp", width=1920)

        cmd = build_rpicam_still_cmd(config, "/tmp/test.jpg")

        assert isinstance(cmd, list)
        for item in cmd:
            assert isinstance(item, str)


class TestMakeOutfile:
    """Test make_outfile() function."""

    def test_creates_output_directory(self, tmp_path):
        """Should create output directory if it doesn't exist."""
        output_dir = tmp_path / "new_dir"
        assert not output_dir.exists()

        config = CameraConfig(
            output_dir=str(output_dir),
            filename_format="%Y%m%d_%H%M%S.jpg",
        )

        make_outfile(config)

        assert output_dir.exists()
        assert output_dir.is_dir()

    def test_generates_timestamped_filename(self, tmp_path):
        """Should generate filename using strftime format."""
        config = CameraConfig(
            output_dir=str(tmp_path),
            filename_format="%Y%m%d.jpg",
        )

        outfile = make_outfile(config)

        filename = Path(outfile).name
        # Should match YYYYMMDD.jpg format
        assert filename.endswith(".jpg")
        assert len(filename) == 12  # 8 digits + .jpg

    def test_expands_tilde_in_output_dir(self, tmp_path, monkeypatch):
        """Should expand ~ in output_dir path."""
        monkeypatch.setenv("HOME", str(tmp_path))

        config = CameraConfig(
            output_dir="~/pictures",
            filename_format="test.jpg",
        )

        outfile = make_outfile(config)

        assert str(tmp_path) in outfile
        assert "~" not in outfile

    def test_returns_absolute_path(self, tmp_path):
        """Should return absolute path string."""
        config = CameraConfig(
            output_dir=str(tmp_path),
            filename_format="image.jpg",
        )

        outfile = make_outfile(config)

        assert Path(outfile).is_absolute()

    def test_creates_nested_directories(self, tmp_path):
        """Should create nested parent directories."""
        nested_dir = tmp_path / "level1" / "level2" / "level3"
        config = CameraConfig(
            output_dir=str(nested_dir),
            filename_format="test.jpg",
        )

        make_outfile(config)

        assert nested_dir.exists()
