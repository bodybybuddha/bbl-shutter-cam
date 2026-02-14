"""Configuration file loading and management.

Handles TOML-based configuration for:
    - Profile management (multiple printers/cameras)
    - Device pairing (MAC address, notify UUID)
    - Camera settings (resolution, exposure, formatting)
    - Trigger event definitions

Configuration file location:
    - Linux/macOS: ~/.config/bbl-shutter-cam/config.toml
    - Windows: %APPDATA%/bbl-shutter-cam/config.toml

Configuration structure:
    [settings]
    default_profile = "office"
    
    [profiles.office]
    [profiles.office.device]
    name = "BBL_SHUTTER"
    mac = "AA:BB:CC:DD:EE:FF"
    notify_uuid = "00002a4d-0000-1000-8000-00805f9b34fb"
    
    [profiles.office.camera]
    output_dir = "~/captures/office"
    [profiles.office.camera.rpicam]
    width = 1920
    height = 1080
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from tomlkit import document, dumps, parse

APP_NAME = "bbl-shutter-cam"
DEFAULT_CONFIG_PATH = Path.home() / ".config" / APP_NAME / "config.toml"


def ensure_config_exists(path: Path = DEFAULT_CONFIG_PATH) -> None:
    """Ensure a config.toml exists; create with defaults if missing.

    Creates parent directories automatically and initializes with a minimal
    "default" profile containing sensible base settings.

    Args:
        path: Path to config.toml file

    Example:
        >>> ensure_config_exists()
        >>> # ~/.config/bbl-shutter-cam/config.toml now exists
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
    """Load and parse the entire TOML configuration file.

    Args:
        path: Path to config.toml file

    Returns:
        Dict-like structure representing the parsed TOML

    Raises:
        FileNotFoundError: If config file doesn't exist

    Example:
        >>> cfg = load_config()
        >>> profiles = cfg.get("profiles", {})
        >>> print(list(profiles.keys()))
        ['office', 'workshop']
    """
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")
    return parse(path.read_text())


def save_config(cfg: Dict[str, Any], path: Path = DEFAULT_CONFIG_PATH) -> None:
    """Write configuration back to disk.

    Creates parent directories if needed. Uses TOML formatting.

    Args:
        cfg: Configuration dictionary to save
        path: Path to write config.toml file to

    Example:
        >>> cfg = load_config()
        >>> cfg["profiles"]["new_printer"] = {...}
        >>> save_config(cfg)
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dumps(cfg))


def load_profile(path: Path, profile_name: str | None) -> Dict[str, Any]:
    """Load a single named profile from the configuration file.

    Resolves default_profile if profile_name is None. Normalizes the returned
    dict to ensure expected sections (device, camera, camera.rpicam) exist.

    Args:
        path: Path to config.toml file
        profile_name: Name of profile to load (e.g., "office"). If None, uses
                     default_profile from config

    Returns:
        Dict: Profile configuration with normalized structure and "_profile_name" key

    Raises:
        FileNotFoundError: If config file doesn't exist
        KeyError: If profile_name is not found or default_profile not set

    Example:
        >>> prof = load_profile(
        ...     Path.home() / ".config" / "bbl-shutter-cam" / "config.toml",
        ...     "office",
        ... )
        >>> mac = prof["device"]["mac"]
        >>> width = prof["camera"]["rpicam"]["width"]
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


def get_trigger_events(profile: Dict[str, Any]) -> list[Dict[str, Any]]:
    """Get trigger event definitions from a profile.

    Retrieves configured trigger signals that should cause photo capture.
    If no events are explicitly configured, returns hardware defaults for
    backward compatibility (manual button press and Bambu Studio triggers).

    Args:
        profile: Profile dict (from load_profile())

    Returns:
        List of event dicts, each containing:
            - hex: Hex string (e.g., "4000")
            - capture: Bool, whether to capture on this event
            - name: Optional event name (e.g., "manual_button")
            - uuid: Characteristic UUID that generated the signal

    Example:
        >>> prof = load_profile(path, "office")
        >>> events = get_trigger_events(prof)
        >>> for evt in events:
        ...     if evt["capture"]:
        ...         print(f"Capture on {evt['hex']}: {evt['name']}")
    """
    device = profile.get("device", {}) or {}
    events = device.get("events", [])

    # If no events configured, return hardware defaults for compatibility
    if not events:
        # Default trigger signals for BBL_SHUTTER / Bambu devices
        return [
            {
                "uuid": "00002a4d-0000-1000-8000-00805f9b34fb",
                "hex": "4000",
                "capture": True,
                "name": "manual_button",
            },
            {
                "uuid": "00002a4d-0000-1000-8000-00805f9b34fb",
                "hex": "8000",
                "capture": True,
                "name": "bambu_studio",
            },
            {
                "uuid": "00002a4d-0000-1000-8000-00805f9b34fb",
                "hex": "0000",
                "capture": False,
                "name": "release",
            },
        ]

    return events


def get_event_trigger_bytes(profile: Dict[str, Any]) -> list[bytes]:
    """Get all configured trigger byte sequences that should capture photos.

    Extracts and converts hex-string trigger events to bytes. Skips any events
    that don't have capture=True or have invalid hex format.

    Args:
        profile: Profile dict (from load_profile())

    Returns:
        List of bytes objects (e.g., [b"@\x00", b"\x80\x00"])

    Example:
        >>> prof = load_profile(path, "office")
        >>> triggers = get_event_trigger_bytes(prof)
        >>> if notification_data in triggers:
        ...     capture_photo()
    """
    events = get_trigger_events(profile)
    triggers = []
    for event in events:
        if event.get("capture", False):
            try:
                hex_str = event.get("hex", "")
                # Convert hex string like "4000" to bytes
                trigger_bytes = bytes.fromhex(hex_str)
                triggers.append(trigger_bytes)
            except ValueError:
                continue
    return triggers


def update_profile_device_fields(
    path: Path,
    profile_name: str,
    mac: str,
    notify_uuid: str,
) -> None:
    """Update or create device pairing information for a profile.

    Stores the device MAC address and notify characteristic UUID in the
    profile. Also sets this profile as the default_profile.

    Args:
        path: Path to config.toml file
        profile_name: Name of profile to update (created if new)
        mac: Device MAC address (e.g., "AA:BB:CC:DD:EE:FF")
        notify_uuid: UUID of the characteristic that sends shutter signals

    Example:
        >>> update_profile_device_fields(
        ...     Path.home() / ".config/bbl-shutter-cam/config.toml",
        ...     "office",
        ...     "AA:BB:CC:DD:EE:FF",
        ...     "00002a4d-0000-1000-8000-00805f9b34fb"
        ... )
        >>> # Now ~/.config/bbl-shutter-cam/config.toml has these settings
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
