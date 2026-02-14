"""Interactive camera calibration and tuning.

Provides an interactive, headless-friendly menu system for tuning camera
settings. Users can:
    - Adjust orientation, focus, exposure, color, and advanced settings
    - Take test photos and inspect results
    - Save validated settings back to profile configuration
    - Rollback changes if needed

All tuning is done via keyboard input without graphical dependencies,
making it suitable for SSH/headless operation.
"""
from __future__ import annotations

import subprocess
import sys
from dataclasses import asdict, replace
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from .camera import CameraConfig, build_rpicam_still_cmd, camera_config_from_profile
from .config import DEFAULT_CONFIG_PATH, load_config, load_profile, save_config
from .util import LOG


class TuningSession:
    """Interactive camera tuning session.

    Manages the state of a tuning session, including current settings,
    test photo counter, and configuration persistence.

    Attributes:
        config_path: Path to config.toml file
        profile_name: Name of profile being tuned
        profile: Full profile dict
        cam_config: Current camera configuration (mutable via replace())
        original_config: Original camera config for rollback
        test_counter: Counter for test photo numbering
        test_dir: Directory for test photos
    """

    def __init__(self, config_path: Path, profile_name: str):
        """Initialize a tuning session.

        Args:
            config_path: Path to config.toml
            profile_name: Profile name to tune
        """
        self.config_path = config_path
        self.profile_name = profile_name
        self.profile = load_profile(config_path, profile_name)
        self.cam_config = camera_config_from_profile(self.profile)
        self.original_config = self.cam_config
        self.test_counter = 0

        # Create test photo directory
        self.test_dir = Path(self.cam_config.output_dir).expanduser() / "tune"
        self.test_dir.mkdir(parents=True, exist_ok=True)

    def update_setting(self, **kwargs) -> None:
        """Update camera settings by replacing the config.

        Args:
            **kwargs: Camera setting key-value pairs to update
        """
        self.cam_config = replace(self.cam_config, **kwargs)

    def take_test_photo(self) -> Optional[str]:
        """Capture a test photo with current settings.

        Returns:
            Path to captured photo, or None if capture failed
        """
        self.test_counter += 1
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"tune_{self.test_counter:03d}_{timestamp}.jpg"
        outfile = str(self.test_dir / filename)

        cmd = build_rpicam_still_cmd(self.cam_config, outfile)
        LOG.debug(f"Capture cmd: {' '.join(cmd)}")

        try:
            subprocess.run(cmd, check=True, capture_output=True)
            return outfile
        except subprocess.CalledProcessError as e:
            LOG.error(f"Capture failed: {e}")
            if e.stderr:
                LOG.error(f"stderr: {e.stderr.decode()}")
            return None

    def save_to_profile(self) -> None:
        """Save current camera settings to profile configuration."""
        cfg = load_config(self.config_path)

        # Navigate to profile's rpicam settings
        prof = cfg.get("profiles", {}).get(self.profile_name)
        if not prof:
            raise ValueError(f"Profile '{self.profile_name}' not found")

        if "camera" not in prof:
            prof["camera"] = {}
        if "rpicam" not in prof["camera"]:
            prof["camera"]["rpicam"] = {}

        rpicam = prof["camera"]["rpicam"]

        # Update all tunable settings
        tunable_fields = [
            "width",
            "height",
            "rotation",
            "hflip",
            "vflip",
            "awb",
            "ev",
            "denoise",
            "sharpness",
            "shutter",
            "gain",
            "awbgains",
            "saturation",
            "contrast",
            "brightness",
            "metering",
            "autofocus_mode",
            "lens_position",
            "quality",
            "timeout",
        ]

        for field in tunable_fields:
            value = getattr(self.cam_config, field)
            if value is not None:
                rpicam[field] = value

        save_config(cfg, self.config_path)
        LOG.info(f"Saved settings to profile '{self.profile_name}'")

    def rollback(self) -> None:
        """Restore original camera settings."""
        self.cam_config = self.original_config
        LOG.info("Rolled back to original settings")

    def show_current_settings(self) -> None:
        """Display current camera settings."""
        print(f"\n{'='*60}")
        print(f"Camera Settings: {self.profile_name}")
        print(f"{'='*60}")
        print(f"Test photos: {self.test_dir}")
        print(f"Photos taken: {self.test_counter}")
        print()

        print("RESOLUTION & ORIENTATION:")
        print(f"  Resolution: {self.cam_config.width}x{self.cam_config.height}")
        print(
            f"  Rotation:   {self.cam_config.rotation if self.cam_config.rotation is not None else 'default (0)'}"
        )
        print(f"  H-Flip:     {self.cam_config.hflip}")
        print(f"  V-Flip:     {self.cam_config.vflip}")
        print()

        print("FOCUS:")
        print(f"  AF Mode:    {self.cam_config.autofocus_mode or 'default'}")
        print(
            f"  Lens Pos:   {self.cam_config.lens_position if self.cam_config.lens_position is not None else 'auto'}"
        )
        print()

        print("EXPOSURE & COLOR:")
        print(f"  EV:         {self.cam_config.ev if self.cam_config.ev is not None else '0'}")
        print(f"  AWB:        {self.cam_config.awb or 'auto'}")
        print(
            f"  Saturation: {self.cam_config.saturation if self.cam_config.saturation is not None else 'default'}"
        )
        print(
            f"  Contrast:   {self.cam_config.contrast if self.cam_config.contrast is not None else 'default'}"
        )
        print(
            f"  Brightness: {self.cam_config.brightness if self.cam_config.brightness is not None else 'default'}"
        )
        print(
            f"  Sharpness:  {self.cam_config.sharpness if self.cam_config.sharpness is not None else 'default'}"
        )
        print()

        print("ADVANCED:")
        print(f"  Denoise:    {self.cam_config.denoise or 'default'}")
        print(f"  Metering:   {self.cam_config.metering or 'default'}")
        print(
            f"  Quality:    {self.cam_config.quality if self.cam_config.quality is not None else 'default (93)'}"
        )
        print(
            f"  Shutter:    {self.cam_config.shutter if self.cam_config.shutter is not None else 'auto'} µs"
        )
        print(
            f"  Gain:       {self.cam_config.gain if self.cam_config.gain is not None else 'auto'}"
        )
        print()


def run_tuning_menu(session: TuningSession) -> None:
    """Run the interactive tuning menu.

    Displays menu and processes user input until exit.

    Args:
        session: Active TuningSession instance
    """
    while True:
        session.show_current_settings()

        print("=" * 60)
        print("TUNING MENU")
        print("=" * 60)
        print()
        print("ORIENTATION:")
        print("  [r] Rotation       [h] H-Flip         [v] V-Flip")
        print()
        print("FOCUS:")
        print("  [f] AF Mode        [l] Lens Position")
        print()
        print("EXPOSURE & COLOR:")
        print("  [e] EV             [a] AWB Mode       [sa] Saturation")
        print("  [co] Contrast      [br] Brightness    [sh] Sharpness")
        print()
        print("ADVANCED:")
        print("  [d] Denoise        [m] Metering       [q] Quality")
        print("  [su] Shutter       [g] Gain")
        print()
        print("ACTIONS:")
        print("  [t] Take test photo")
        print("  [s] Save & exit")
        print("  [x] Exit without saving")
        print("  [z] Rollback to original")
        print()

        choice = input("Choose option: ").strip().lower()

        if choice == "t":
            handle_test_photo(session)
        elif choice == "s":
            handle_save_and_exit(session)
            break
        elif choice == "x":
            print("\nExiting without saving...")
            break
        elif choice == "z":
            session.rollback()
            print("\n✓ Rolled back to original settings")
        elif choice == "r":
            handle_rotation(session)
        elif choice == "h":
            handle_hflip(session)
        elif choice == "v":
            handle_vflip(session)
        elif choice == "f":
            handle_autofocus_mode(session)
        elif choice == "l":
            handle_lens_position(session)
        elif choice == "e":
            handle_ev(session)
        elif choice == "a":
            handle_awb(session)
        elif choice == "sa":
            handle_saturation(session)
        elif choice == "co":
            handle_contrast(session)
        elif choice == "br":
            handle_brightness(session)
        elif choice == "sh":
            handle_sharpness(session)
        elif choice == "d":
            handle_denoise(session)
        elif choice == "m":
            handle_metering(session)
        elif choice == "q":
            handle_quality(session)
        elif choice == "su":
            handle_shutter(session)
        elif choice == "g":
            handle_gain(session)
        else:
            print(f"\nUnknown option: {choice}")

        print("\nPress Enter to continue...")
        input()


def handle_test_photo(session: TuningSession) -> None:
    """Capture a test photo."""
    print("\nCapturing test photo...")
    outfile = session.take_test_photo()
    if outfile:
        print(f"✓ Photo saved: {outfile}")
        print(f"  Use SFTP/SCP to view: scp pi@{{}}.local:{outfile} .")
    else:
        print("✗ Capture failed. Check logs.")


def handle_save_and_exit(session: TuningSession) -> None:
    """Save settings and exit."""
    print("\nSaving settings to profile...")
    try:
        session.save_to_profile()
        print(f"✓ Settings saved to {session.config_path}")
        print(f"  Profile: {session.profile_name}")
    except Exception as e:
        LOG.error(f"Failed to save: {e}")
        print(f"✗ Save failed: {e}")


def handle_rotation(session: TuningSession) -> None:
    """Handle rotation setting."""
    print("\nRotation (0, 90, 180, 270):")
    val = input(
        "Enter value [current: {}]: ".format(
            session.cam_config.rotation if session.cam_config.rotation is not None else "0"
        )
    ).strip()

    if val:
        try:
            rot = int(val)
            if rot not in [0, 90, 180, 270]:
                print("✗ Must be 0, 90, 180, or 270")
                return
            session.update_setting(rotation=rot)
            print(f"✓ Rotation set to {rot}")
        except ValueError:
            print("✗ Invalid number")


def handle_hflip(session: TuningSession) -> None:
    """Toggle horizontal flip."""
    new_val = not session.cam_config.hflip
    session.update_setting(hflip=new_val)
    print(f"\n✓ H-Flip: {new_val}")


def handle_vflip(session: TuningSession) -> None:
    """Toggle vertical flip."""
    new_val = not session.cam_config.vflip
    session.update_setting(vflip=new_val)
    print(f"\n✓ V-Flip: {new_val}")


def handle_autofocus_mode(session: TuningSession) -> None:
    """Handle autofocus mode setting."""
    current = session.cam_config.autofocus_mode or "auto"
    print("\nAutofocus Mode:")
    print(f"  1. auto{' ←' if current == 'auto' else ' (default)'}")
    print(f"  2. manual{' ←' if current == 'manual' else ''}")
    print(f"  3. continuous{' ←' if current == 'continuous' else ''}")
    choice = input("Choose [1-3]: ").strip()

    modes = {"1": "auto", "2": "manual", "3": "continuous"}
    if choice in modes:
        session.update_setting(autofocus_mode=modes[choice])
        print(f"✓ AF Mode: {modes[choice]}")
    else:
        print("✗ Invalid choice")


def handle_lens_position(session: TuningSession) -> None:
    """Handle lens position setting."""
    current = (
        session.cam_config.lens_position if session.cam_config.lens_position is not None else "auto"
    )
    print("\nLens Position (0.0=infinity to ~32.0=close):")
    print("  Typical values: 0.0 (far), 2.0 (mid), 8.0 (near)")
    val = input(f"Enter value [current: {current}]: ").strip()

    if val:
        try:
            pos = float(val)
            if pos < 0 or pos > 100:
                print("✗ Out of range")
                return
            session.update_setting(lens_position=pos)
            print(f"✓ Lens position: {pos}")
        except ValueError:
            print("✗ Invalid number")


def handle_ev(session: TuningSession) -> None:
    """Handle exposure compensation."""
    print("\nExposure Compensation (-10 to +10):")
    val = input(
        "Enter value [current: {}]: ".format(
            session.cam_config.ev if session.cam_config.ev is not None else "0"
        )
    ).strip()

    if val:
        try:
            ev = int(val)
            if ev < -10 or ev > 10:
                print("✗ Out of range")
                return
            session.update_setting(ev=ev)
            print(f"✓ EV: {ev}")
        except ValueError:
            print("✗ Invalid number")


def handle_awb(session: TuningSession) -> None:
    """Handle auto white balance mode."""
    current = session.cam_config.awb or "auto"
    print("\nAuto White Balance:")
    print(f"  1. auto{' ←' if current == 'auto' else ' (default)'}")
    print(f"  2. daylight{' ←' if current == 'daylight' else ''}")
    print(f"  3. tungsten{' ←' if current == 'tungsten' else ''}")
    print(f"  4. fluorescent{' ←' if current == 'fluorescent' else ''}")
    print(f"  5. indoor{' ←' if current == 'indoor' else ''}")
    print(f"  6. cloudy{' ←' if current == 'cloudy' else ''}")
    choice = input("Choose [1-6]: ").strip()

    modes = {
        "1": "auto",
        "2": "daylight",
        "3": "tungsten",
        "4": "fluorescent",
        "5": "indoor",
        "6": "cloudy",
    }

    if choice in modes:
        session.update_setting(awb=modes[choice])
        print(f"✓ AWB: {modes[choice]}")
    else:
        print("✗ Invalid choice")


def handle_saturation(session: TuningSession) -> None:
    """Handle saturation setting."""
    current = (
        session.cam_config.saturation
        if session.cam_config.saturation is not None
        else "1.0 (default)"
    )
    print(f"\nSaturation (0.0 to 2.0, default 1.0):")
    val = input(f"Enter value [current: {current}]: ").strip()

    if val:
        try:
            sat = float(val)
            if sat < 0 or sat > 2:
                print("✗ Out of range")
                return
            session.update_setting(saturation=sat)
            print(f"✓ Saturation: {sat}")
        except ValueError:
            print("✗ Invalid number")


def handle_contrast(session: TuningSession) -> None:
    """Handle contrast setting."""
    current = (
        session.cam_config.contrast if session.cam_config.contrast is not None else "1.0 (default)"
    )
    print(f"\nContrast (0.0 to 2.0, default 1.0):")
    val = input(f"Enter value [current: {current}]: ").strip()

    if val:
        try:
            con = float(val)
            if con < 0 or con > 2:
                print("✗ Out of range")
                return
            session.update_setting(contrast=con)
            print(f"✓ Contrast: {con}")
        except ValueError:
            print("✗ Invalid number")


def handle_brightness(session: TuningSession) -> None:
    """Handle brightness setting."""
    current = (
        session.cam_config.brightness
        if session.cam_config.brightness is not None
        else "0.0 (default)"
    )
    print(f"\nBrightness (-1.0 to 1.0, default 0.0):")
    val = input(f"Enter value [current: {current}]: ").strip()

    if val:
        try:
            br = float(val)
            if br < -1 or br > 1:
                print("✗ Out of range")
                return
            session.update_setting(brightness=br)
            print(f"✓ Brightness: {br}")
        except ValueError:
            print("✗ Invalid number")


def handle_sharpness(session: TuningSession) -> None:
    """Handle sharpness setting."""
    current = (
        session.cam_config.sharpness
        if session.cam_config.sharpness is not None
        else "1.0 (default)"
    )
    print(f"\nSharpness (0.0 to 2.0, default 1.0):")
    val = input(f"Enter value [current: {current}]: ").strip()

    if val:
        try:
            sharp = float(val)
            if sharp < 0 or sharp > 2:
                print("✗ Out of range")
                return
            session.update_setting(sharpness=sharp)
            print(f"✓ Sharpness: {sharp}")
        except ValueError:
            print("✗ Invalid number")


def handle_denoise(session: TuningSession) -> None:
    """Handle denoise mode."""
    current = session.cam_config.denoise or "cdn_off"
    print("\nDenoise Mode:")
    print(f"  1. off{' ←' if current == 'off' else ''}")
    print(f"  2. cdn_off{' ←' if current == 'cdn_off' else ' (default)'}")
    print(f"  3. cdn_fast{' ←' if current == 'cdn_fast' else ''}")
    print(f"  4. cdn_hq{' ←' if current == 'cdn_hq' else ''}")
    choice = input("Choose [1-4]: ").strip()

    modes = {"1": "off", "2": "cdn_off", "3": "cdn_fast", "4": "cdn_hq"}

    if choice in modes:
        session.update_setting(denoise=modes[choice])
        print(f"✓ Denoise: {modes[choice]}")
    else:
        print("✗ Invalid choice")


def handle_metering(session: TuningSession) -> None:
    """Handle metering mode."""
    current = session.cam_config.metering or "centre"
    print("\nMetering Mode:")
    print(f"  1. centre{' ←' if current == 'centre' else ' (default)'}")
    print(f"  2. spot{' ←' if current == 'spot' else ''}")
    print(f"  3. matrix{' ←' if current == 'matrix' else ''}")
    print(f"  4. custom{' ←' if current == 'custom' else ''}")
    choice = input("Choose [1-4]: ").strip()

    modes = {"1": "centre", "2": "spot", "3": "matrix", "4": "custom"}

    if choice in modes:
        session.update_setting(metering=modes[choice])
        print(f"✓ Metering: {modes[choice]}")
    else:
        print("✗ Invalid choice")


def handle_quality(session: TuningSession) -> None:
    """Handle JPEG quality."""
    current = (
        session.cam_config.quality if session.cam_config.quality is not None else "93 (default)"
    )
    print(f"\nJPEG Quality (0-100, default 93):")
    val = input(f"Enter value [current: {current}]: ").strip()

    if val:
        try:
            qual = int(val)
            if qual < 0 or qual > 100:
                print("✗ Out of range")
                return
            session.update_setting(quality=qual)
            print(f"✓ Quality: {qual}")
        except ValueError:
            print("✗ Invalid number")


def handle_shutter(session: TuningSession) -> None:
    """Handle shutter speed."""
    current = session.cam_config.shutter if session.cam_config.shutter is not None else "auto"
    print("\nShutter Speed (microseconds, e.g., 10000 = 1/100s):")
    print("  Leave empty for auto")
    val = input(f"Enter value [current: {current}]: ").strip()

    if val:
        try:
            shutter = int(val)
            if shutter < 0:
                print("✗ Must be positive")
                return
            session.update_setting(shutter=shutter)
            print(f"✓ Shutter: {shutter} µs")
        except ValueError:
            print("✗ Invalid number")


def handle_gain(session: TuningSession) -> None:
    """Handle analog gain."""
    current = session.cam_config.gain if session.cam_config.gain is not None else "auto"
    print("\nAnalog Gain (typically 1.0-16.0):")
    print("  Leave empty for auto")
    val = input(f"Enter value [current: {current}]: ").strip()

    if val:
        try:
            gain = float(val)
            if gain < 0:
                print("✗ Must be positive")
                return
            session.update_setting(gain=gain)
            print(f"✓ Gain: {gain}")
        except ValueError:
            print("✗ Invalid number")


def tune_profile(config_path: Path, profile_name: str) -> int:
    """Main entry point for interactive tuning.

    Args:
        config_path: Path to config.toml
        profile_name: Profile name to tune

    Returns:
        0 on success, 1 on error
    """
    try:
        session = TuningSession(config_path, profile_name)

        print("\n" + "=" * 60)
        print("INTERACTIVE CAMERA TUNING")
        print("=" * 60)
        print(f"Profile: {profile_name}")
        print(f"Config:  {config_path}")
        print(f"Test photos will be saved to: {session.test_dir}")
        print()
        print("TIP: Use SFTP/SCP to view test photos on your computer")
        print("     Example: scp pi@pi5.local:~/captures/*/tune/*.jpg .")
        print()
        input("Press Enter to start tuning...")

        run_tuning_menu(session)

        return 0

    except Exception as e:
        LOG.error(f"Tuning failed: {e}")
        print(f"\n✗ Error: {e}")
        return 1
