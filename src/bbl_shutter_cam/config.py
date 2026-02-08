# src/bbl_shutter_cam/config.py
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from tomlkit import document, dumps, parse

APP_NAME = "bbl-shutter-cam"
DEFAULT_CONFIG_PATH = Path.home() / ".config" / APP_NAME / "config.toml"


def ensure_config_exists(path: Path = DEFAULT_CONFIG_PATH) -> None:
    """
    Ensure a config.toml exists. If missing, create a minimal default.
    """
    if path.exists():
        return

    path.parent.mkdir(parents=True, exist_ok=True)

    cfg = document()
    cfg["default_profile"] = "default"
    cfg["profiles"] = document()

    # Minimal default profile
    cfg["profiles"]["default"] = document()
    cfg["profiles"]["default"]["device"] = {
        "name": "BBL_SHUTTER",
        # mac and notify_uuid learned during setup
    }
    cfg["profiles"]["default"]["camera"] = {
        "output_dir": str(Path.home() / "captures" / "default"),
        "filename_format": "%Y%m%d_%H%M%S.jpg",
        "min_interval_sec": 0.5,
        "rpicam": {
            "width": 1920,
            "height": 1080,
            "nopreview": True,
        },
    }

    path.write_text(dumps(cfg))


def load_config(path: Path = DEFAULT_CONFIG_PATH) -> Dict[str, Any]:
    """
    Load the entire TOML config as a dict-like structure.
    """
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")
    return parse(path.read_text())


def save_config(cfg: Dict[str, Any], path: Path = DEFAULT_CONFIG_PATH) -> None:
    """
    Write config back to disk.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dumps(cfg))


def load_profile(path: Path, profile_name: str | None) -> Dict[str, Any]:
    """
    Load and return a single profile dict, resolving default_profile if needed.
    """
    cfg = load_config(path)

    profiles = cfg.get("profiles")
    if not profiles:
        raise KeyError("No [profiles] section found in config.")

    if profile_name is None:
        profile_name = cfg.get("default_profile")
        if not profile_name:
            raise KeyError("No profile specified and no default_profile set.")

    if profile_name not in profiles:
        raise KeyError(f"Profile '{profile_name}' not found in config.")

    prof = profiles[profile_name]

    # Normalize expected sections
    prof.setdefault("device", {})
    prof.setdefault("camera", {})
    prof["camera"].setdefault("rpicam", {})

    # Attach resolved name for convenience
    prof["_profile_name"] = profile_name

    return prof


def update_profile_device_fields(
    path: Path,
    profile_name: str,
    mac: str,
    notify_uuid: str,
) -> None:
    """
    Update (or create) the device fields for a profile.
    """
    cfg = load_config(path)

    profiles = cfg.setdefault("profiles", document())
    prof = profiles.setdefault(profile_name, document())
    device = prof.setdefault("device", document())

    device["mac"] = mac
    device["notify_uuid"] = notify_uuid

    # Set as default profile
    cfg["default_profile"] = profile_name

    save_config(cfg, path)
