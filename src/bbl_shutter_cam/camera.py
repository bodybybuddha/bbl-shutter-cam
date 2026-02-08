# src/bbl_shutter_cam/camera.py
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class CameraConfig:
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


def camera_config_from_profile(profile: Dict[str, Any]) -> CameraConfig:
    """
    Read camera configuration from a profile dict (from config.py load_profile()).
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
    )


def make_outfile(cam: CameraConfig) -> str:
    """
    Return a fully-qualified output filename, ensuring output_dir exists.
    """
    out_dir = Path(cam.output_dir).expanduser()
    out_dir.mkdir(parents=True, exist_ok=True)
    name = datetime.now().strftime(cam.filename_format)
    return str(out_dir / name)


def build_rpicam_still_cmd(cam: CameraConfig, outfile: str) -> List[str]:
    """
    Build an rpicam-still command based on CameraConfig.
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

    return cmd
