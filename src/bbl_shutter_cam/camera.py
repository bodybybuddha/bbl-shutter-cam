"""Camera capture and configuration management.

Provides structures and utilities for:
    - Configuring rpicam-still capture parameters
    - Loading camera settings from TOML profiles
    - Building rpicam-still command-line invocations
    - Managing output file naming and directories

All camera settings are exposed as configuration options with sensible defaults.
"""

from __future__ import annotations

import asyncio
import subprocess
import threading
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

# Serializes access to the physical camera device across the BLE-triggered
# capture path and any web-triggered capture (e.g. streaming.py), since
# rpicam-still (and rpicam-vid, for streaming.py's MJPEG stream) can only
# use the camera exclusively.
CAMERA_LOCK = threading.Lock()


class LatestFrame:
    """Thread-safe cache of the most recent frame from an active MJPEG stream.

    streaming.py updates this as it reads frames from rpicam-vid while a
    /stream client is connected. capture_still_sync()/capture_preview_sync()
    check it first so a BLE press or manual capture during an active stream
    reuses that frame instead of trying to run rpicam-still while rpicam-vid
    already has exclusive use of the camera.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._data: Optional[bytes] = None
        self._timestamp: float = 0.0

    def update(self, data: bytes) -> None:
        """Record a newly-decoded stream frame."""
        with self._lock:
            self._data = data
            self._timestamp = time.monotonic()

    def get_if_fresh(self, max_age: float = 2.0) -> Optional[bytes]:
        """Return the cached frame if it's newer than max_age seconds, else None."""
        with self._lock:
            if self._data is not None and (time.monotonic() - self._timestamp) <= max_age:
                return self._data
            return None

    def clear(self) -> None:
        """Drop the cached frame, e.g. when the stream stops."""
        with self._lock:
            self._data = None


# Module-level singleton: one camera, one process, one cache.
LATEST_FRAME = LatestFrame()


class StreamController:
    """Bridge between an active MJPEG stream (owned by streaming.py) and the
    BLE-triggered / manual capture paths (owned by discover.py / streaming.py's
    /capture route), without camera.py importing streaming.py.

    streaming.py is only imported when the optional "web" extra is installed
    and --web-port is used, so camera.py (always imported) can't depend on
    it directly. Instead, streaming.py registers a callable here while a
    stream with capture_mode="pause" is active; capture code calls
    request_pause_capture() and cooperates with whatever it gets back
    instead of racing rpicam-vid for the camera device.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._pause_and_capture: Optional[Callable[[], str]] = None

    def register(self, pause_and_capture: Callable[[], str]) -> None:
        """Register the active stream's pause-and-capture callable."""
        with self._lock:
            self._pause_and_capture = pause_and_capture

    def unregister(self) -> None:
        """Clear the registration, e.g. when the stream stops."""
        with self._lock:
            self._pause_and_capture = None

    def request_pause_capture(self) -> Optional[str]:
        """If a "pause"-mode stream is active, pause it, take a full-quality
        still, and return its path. Returns None if nothing is registered
        (caller should fall back to a normal capture)."""
        with self._lock:
            fn = self._pause_and_capture
        if fn is None:
            return None
        return fn()


# Module-level singleton, same rationale as LATEST_FRAME.
STREAM_CONTROLLER = StreamController()


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

    awb: Optional[str] = None  # e.g. "auto", "daylight", "tungsten"
    ev: Optional[int] = None  # exposure compensation integer
    denoise: Optional[str] = None  # e.g. "cdn_off"
    sharpness: Optional[float] = None

    # Manual-ish “locks” (set these to freeze exposure/white balance)
    shutter: Optional[int] = None  # microseconds
    gain: Optional[float] = None
    awbgains: Optional[str] = None  # "1.5,1.8"
    # Color & Tone adjustments
    saturation: Optional[float] = None  # 0.0-2.0
    contrast: Optional[float] = None  # 0.0-2.0
    brightness: Optional[float] = None  # -1.0 to 1.0

    # Metering & Focus
    metering: Optional[str] = None  # "centre", "spot", "matrix", "custom"
    autofocus_mode: Optional[str] = None  # "auto", "manual", "continuous"
    lens_position: Optional[float] = None  # 0.0 (infinity) to ~32.0 (close)

    # Capture settings
    quality: Optional[int] = None  # JPEG quality 0-100
    timeout: Optional[int] = None  # milliseconds


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

    # Default output_dir includes profile name to prevent file collision
    profile_name = profile.get("_profile_name", "default")
    default_output = str(Path.home() / "captures" / profile_name)
    output_dir = cam.get("output_dir", default_output)
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


@dataclass(frozen=True)
class StreamConfig:
    """Configuration for the optional live MJPEG stream (/stream endpoint).

    Deliberately separate from CameraConfig: streaming uses rpicam-vid, a
    different tool from rpicam-still, with its own resolution/framerate
    tradeoffs (lower-spec by default so it stays light on a Pi Zero 2W).
    Orientation (rotation/hflip/vflip) is shared with CameraConfig instead
    of duplicated here, since it describes the physical camera mount, not
    a stream-specific choice.

    Attributes:
        width: Stream width in pixels
        height: Stream height in pixels
        fps: Target stream frame rate
        quality: MJPEG JPEG quality (0-100)
        timeout_seconds: Auto-stop the stream after this many seconds,
            even if a client is still connected
    """

    width: int = 640
    height: int = 480
    fps: int = 12
    quality: int = 80
    timeout_seconds: float = 300.0
    capture_mode: str = "frame"  # "frame" (grab current stream frame) or "pause"


def stream_config_from_profile(profile: Dict[str, Any]) -> StreamConfig:
    """Load stream configuration from a profile dictionary.

    Reads the optional [profiles.<name>.server] section. All settings are
    optional with Pi Zero 2W-friendly defaults, per docs/advanced/web-streaming.md.

    Args:
        profile: Profile dictionary, as from config.py's load_profile().

    Returns:
        StreamConfig: Configured stream settings with defaults applied.
    """
    server = profile.get("server", {}) or {}

    resolution = str(server.get("stream_resolution", "640x480"))
    try:
        width_str, height_str = resolution.lower().split("x", 1)
        width, height = int(width_str), int(height_str)
    except ValueError as exc:
        raise ValueError(
            f"Invalid stream_resolution {resolution!r}; expected e.g. '640x480'"
        ) from exc

    capture_mode = str(server.get("capture_mode", "frame")).lower()
    if capture_mode not in ("frame", "pause"):
        raise ValueError(f"Invalid capture_mode {capture_mode!r}; expected 'frame' or 'pause'")

    return StreamConfig(
        width=width,
        height=height,
        fps=int(server.get("stream_fps", 12)),
        quality=int(server.get("jpeg_quality", 80)),
        timeout_seconds=float(server.get("stream_timeout_seconds", 300)),
        capture_mode=capture_mode,
    )


def build_rpicam_vid_mjpeg_cmd(stream_cfg: StreamConfig, cam: CameraConfig) -> List[str]:
    """Build an rpicam-vid command that writes an MJPEG stream to stdout.

    Orientation is taken from the still-capture CameraConfig so the stream
    matches the physical camera mount without needing its own setting.

    Args:
        stream_cfg: Stream resolution/framerate/quality settings.
        cam: CameraConfig to source rotation/hflip/vflip from.

    Returns:
        List[str]: Complete command-line as list (ready for subprocess).
    """
    cmd: List[str] = [
        "rpicam-vid",
        "-t",
        "0",  # run until killed
        "--codec",
        "mjpeg",
        "-o",
        "-",  # stdout
        "--width",
        str(stream_cfg.width),
        "--height",
        str(stream_cfg.height),
        "--framerate",
        str(stream_cfg.fps),
        "--quality",
        str(stream_cfg.quality),
        "--nopreview",
        "--flush",
    ]

    if cam.rotation is not None:
        cmd += ["--rotation", str(cam.rotation)]
    if cam.hflip:
        cmd.append("--hflip")
    if cam.vflip:
        cmd.append("--vflip")

    return cmd


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


def capture_still_sync(cam: CameraConfig, capture_mode: str = "frame") -> str:
    """Capture a photo into the profile's normal numbered output sequence.

    If an MJPEG stream is currently active (see LATEST_FRAME/StreamController
    in this module, and streaming.py), cooperates with it instead of trying
    to run rpicam-still while rpicam-vid has the camera:
        - capture_mode="frame" (default): reuse the most recent stream frame
          if it's fresh (fast, no interruption, but stream resolution rather
          than full still resolution).
        - capture_mode="pause": ask the stream to pause, take a full-quality
          still, then resume the stream.
    Falls back to a normal rpicam-still capture if no stream is active.

    Blocks the calling thread for the duration of the capture. Serializes
    against other callers via CAMERA_LOCK so a web-triggered capture can't
    collide with a BLE-triggered one.

    Args:
        cam: CameraConfig with capture parameters
        capture_mode: "frame" or "pause"; see above. Ignored if no stream
            is currently active.

    Returns:
        str: Path to the captured JPEG.

    Raises:
        subprocess.CalledProcessError: If rpicam-still fails.
    """
    if capture_mode == "pause":
        paused_outfile = STREAM_CONTROLLER.request_pause_capture()
        if paused_outfile is not None:
            return paused_outfile
    else:
        frame = LATEST_FRAME.get_if_fresh()
        if frame is not None:
            outfile = make_outfile(cam)
            Path(outfile).write_bytes(frame)
            return outfile

    outfile = make_outfile(cam)
    cmd = build_rpicam_still_cmd(cam, outfile)
    with CAMERA_LOCK:
        subprocess.run(cmd, check=True, capture_output=True)
    return outfile


def capture_preview_sync(cam: CameraConfig) -> str:
    """Capture a lightweight preview snapshot, overwriting the same file each time.

    Unlike capture_still_sync(), this does not add a new file to the profile's
    numbered capture sequence — it's meant for on-demand web preview, not
    for the time-lapse archive. Always prefers a fresh stream frame if one's
    available (pausing the stream just to preview it would be self-defeating),
    falling back to rpicam-still if no stream is active.

    Args:
        cam: CameraConfig with capture parameters

    Returns:
        str: Path to the (overwritten) preview JPEG.

    Raises:
        subprocess.CalledProcessError: If rpicam-still fails.
    """
    out_dir = Path(cam.output_dir).expanduser() / "web"
    out_dir.mkdir(parents=True, exist_ok=True)
    outfile = str(out_dir / "snapshot.jpg")

    frame = LATEST_FRAME.get_if_fresh()
    if frame is not None:
        Path(outfile).write_bytes(frame)
        return outfile

    cmd = build_rpicam_still_cmd(cam, outfile)
    with CAMERA_LOCK:
        subprocess.run(cmd, check=True, capture_output=True)
    return outfile


async def capture_still(cam: CameraConfig, capture_mode: str = "frame") -> str:
    """Async wrapper for capture_still_sync(); runs in a worker thread so it
    doesn't block the event loop (and thus the BLE listener) for the
    several seconds a capture takes."""
    return await asyncio.to_thread(capture_still_sync, cam, capture_mode)


async def capture_preview(cam: CameraConfig) -> str:
    """Async wrapper for capture_preview_sync(); see capture_still()."""
    return await asyncio.to_thread(capture_preview_sync, cam)
