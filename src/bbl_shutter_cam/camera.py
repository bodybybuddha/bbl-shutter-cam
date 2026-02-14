"""Camera capture and configuration management.

Provides structures and utilities for:
    - Configuring rpicam-still capture parameters
    - Loading camera settings from TOML profiles
    - Building rpicam-still command-line invocations
    - Managing output file naming and directories

All camera settings are exposed as configuration options with sensible defaults.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class CameraConfig:
    """Immutable camera configuration derived from a profile.

    Attributes:
        output_dir: Directory where captured images are stored
        filename_format: strftime format for image filenames (e.g. "%Y%m%d_%H%M%S.jpg")
        min_interval_sec: Minimum time between captures to prevent accidental double-triggers
        width: Image width in pixels
        height: Image height in pixels
        nopreview: Disable camera preview window
        rotation: Image rotation (0, 90, 180, or 270 degrees)
        hflip: Flip image horizontally
        vflip: Flip image vertically
        awb: Auto white balance mode ("auto", "daylight", "tungsten", etc.)
        ev: Exposure compensation (integer, typically -10 to +10)
        denoise: Denoising mode ("cdn_off", "cdn_hq", etc.)
        sharpness: Sharpness adjustment (float, typically -1.0 to 1.0)
        shutter: Shutter speed in microseconds (locks exposure when set)
        gain: Analog gain (locks white balance when set)
        awbgains: White balance gains as "r,b" string (e.g. "1.5,1.8")
        saturation: Saturation adjustment (float, typically 0.0 to 2.0)
        contrast: Contrast adjustment (float, typically 0.0 to 2.0)
        brightness: Brightness adjustment (float, typically -1.0 to 1.0)
        metering: Metering mode ("centre", "spot", "matrix", "custom")
        autofocus_mode: Autofocus mode ("auto", "manual", "continuous")
        lens_position: Manual lens position (float, 0.0=infinity to ~32.0=close)
        quality: JPEG quality (integer, 0-100)
        timeout: Capture timeout in milliseconds
    """
    output_dir: str
    filename_format: str = "%Y%m%d_%H%M%S.jpg"
    min_interval_sec: float = 0.5

    # rpicam-still settings
    width: Optional[int] = 1920
    height: Optional[int] = 1080
    nopreview: bool = True

    rotation: Optional[int] = None  # 0/90/180/270
    hflip: bool = False
    vflip: bool = False

    awb: Optional[str] = None       # e.g. "auto", "daylight", "tungsten"
    ev: Optional[int] = None        # exposure compensation integer
    denoise: Optional[str] = None   # e.g. "cdn_off"
    sharpness: Optional[float] = None

    # Manual-ish “locks” (set these to freeze exposure/white balance)
    shutter: Optional[int] = None      # microseconds
    gain: Optional[float] = None
    awbgains: Optional[str] = None     # "1.5,1.8"
    # Color & Tone adjustments
    saturation: Optional[float] = None  # 0.0-2.0
    contrast: Optional[float] = None    # 0.0-2.0
    brightness: Optional[float] = None  # -1.0 to 1.0

    # Metering & Focus
    metering: Optional[str] = None      # "centre", "spot", "matrix", "custom"
    autofocus_mode: Optional[str] = None  # "auto", "manual", "continuous"
    lens_position: Optional[float] = None # 0.0 (infinity) to ~32.0 (close)

    # Capture settings
    quality: Optional[int] = None       # JPEG quality 0-100
    timeout: Optional[int] = None       # milliseconds

def camera_config_from_profile(profile: Dict[str, Any]) -> CameraConfig:
    """Load camera configuration from a profile dictionary.

    Extracts camera settings from a profile dict (typically from config.py's
    load_profile()). Applies sensible defaults for any missing values.

    Args:
        profile: Profile dictionary containing optional keys:
            - camera.output_dir: Image output directory
            - camera.filename_format: strftime format for filenames
            - camera.min_interval_sec: Minimum seconds between captures
            - camera.rpicam: Dict of rpicam-still options (width, height, etc.)

    Returns:
        CameraConfig: Configured camera settings with defaults applied.

    Example:
        >>> config = load_profile(path, "my-printer")
        >>> cam = camera_config_from_profile(config)
        >>> print(cam.width, cam.height)
        1920 1080
    """
    cam = profile.get("camera", {}) or {}
    rp = cam.get("rpicam", {}) or {}

    output_dir = cam.get("output_dir", str(Path.home() / "captures"))
    filename_format = cam.get("filename_format", "%Y%m%d_%H%M%S.jpg")
    min_interval_sec = float(cam.get("min_interval_sec", 0.5))

    return CameraConfig(
        output_dir=str(output_dir),
        filename_format=str(filename_format),
        min_interval_sec=min_interval_sec,
        width=rp.get("width", 1920),
        height=rp.get("height", 1080),
        nopreview=bool(rp.get("nopreview", True)),
        rotation=rp.get("rotation"),
        hflip=bool(rp.get("hflip", False)),
        vflip=bool(rp.get("vflip", False)),
        awb=rp.get("awb"),
        ev=rp.get("ev"),
        denoise=rp.get("denoise"),
        sharpness=rp.get("sharpness"),
        shutter=rp.get("shutter"),
        gain=rp.get("gain"),
        awbgains=rp.get("awbgains"),
        saturation=rp.get("saturation"),
        contrast=rp.get("contrast"),
        brightness=rp.get("brightness"),
        metering=rp.get("metering"),
        autofocus_mode=rp.get("autofocus_mode"),
        lens_position=rp.get("lens_position"),
        quality=rp.get("quality"),
        timeout=rp.get("timeout"),
    )


def make_outfile(cam: CameraConfig) -> str:
    """Generate output filename and ensure output directory exists.

    Uses the filename_format from config to create a timestamped filename
    in the configured output directory. Creates the directory if it doesn't exist.

    Args:
        cam: CameraConfig instance with output_dir and filename_format

    Returns:
        str: Absolute path to the output file (file does not exist yet)

    Example:
        >>> cam = CameraConfig(output_dir="~/captures", filename_format="%Y%m%d_%H%M%S.jpg")
        >>> path = make_outfile(cam)
        >>> print(path)
        /home/user/captures/20260214_123456.jpg
    """
    out_dir = Path(cam.output_dir).expanduser()
    out_dir.mkdir(parents=True, exist_ok=True)
    name = datetime.now().strftime(cam.filename_format)
    return str(out_dir / name)


def build_rpicam_still_cmd(cam: CameraConfig, outfile: str) -> List[str]:
    """Build an rpicam-still command from camera configuration.

    Constructs the complete command-line arguments for rpicam-still based on
    the configuration. Only includes parameters that are explicitly set
    (None values are omitted).

    Args:
        cam: CameraConfig with capture parameters
        outfile: Output file path (will be passed to -o flag)

    Returns:
        List[str]: Complete command-line as list (ready for subprocess.run)

    Example:
        >>> cam = CameraConfig(width=1920, height=1080, rotation=90)
        >>> cmd = build_rpicam_still_cmd(cam, "/tmp/test.jpg")
        >>> cmd
        ['rpicam-still', '-o', '/tmp/test.jpg', '--width', '1920',
         '--height', '1080', '--rotation', '90', '--nopreview']
    """
    cmd: List[str] = ["rpicam-still", "-o", outfile]

    if cam.nopreview:
        cmd.append("--nopreview")

    # Resolution
    if cam.width is not None:
        cmd += ["--width", str(cam.width)]
    if cam.height is not None:
        cmd += ["--height", str(cam.height)]

    # Orientation
    if cam.rotation is not None:
        cmd += ["--rotation", str(cam.rotation)]
    if cam.hflip:
        cmd.append("--hflip")
    if cam.vflip:
        cmd.append("--vflip")

    # Tuning
    if cam.awb is not None:
        cmd += ["--awb", str(cam.awb)]
    if cam.ev is not None:
        cmd += ["--ev", str(cam.ev)]
    if cam.denoise is not None:
        cmd += ["--denoise", str(cam.denoise)]
    if cam.sharpness is not None:
        cmd += ["--sharpness", str(cam.sharpness)]

    # Manual-ish controls (set these to “lock” exposure/WB)
    if cam.shutter is not None:
        cmd += ["--shutter", str(cam.shutter)]
    if cam.gain is not None:
        cmd += ["--gain", str(cam.gain)]
    if cam.awbgains is not None:
        cmd += ["--awbgains", str(cam.awbgains)]
    # Color & Tone
    if cam.saturation is not None:
        cmd += ["--saturation", str(cam.saturation)]
    if cam.contrast is not None:
        cmd += ["--contrast", str(cam.contrast)]
    if cam.brightness is not None:
        cmd += ["--brightness", str(cam.brightness)]

    # Metering & Focus
    if cam.metering is not None:
        cmd += ["--metering", str(cam.metering)]
    if cam.autofocus_mode is not None:
        cmd += ["--autofocus-mode", str(cam.autofocus_mode)]
    if cam.lens_position is not None:
        cmd += ["--lens-position", str(cam.lens_position)]

    # Capture settings
    if cam.quality is not None:
        cmd += ["--quality", str(cam.quality)]
    if cam.timeout is not None:
        cmd += ["--timeout", str(cam.timeout)]
    return cmd
