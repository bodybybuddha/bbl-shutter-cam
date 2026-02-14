"""Command-line interface for bbl-shutter-cam.

Provides argument parsing and command handlers for:
    - scan: Find nearby BLE devices
    - setup: Configure a new printer profile
    - debug: Discover and log unknown BLE signals
    - run: Listen for shutter signals and capture photos

All commands use async/await for non-blocking BLE operations.
"""
from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

from . import discover, tune
from .config import DEFAULT_CONFIG_PATH, ensure_config_exists, load_profile
from .util import LOG, configure_logging


def _build_parser() -> argparse.ArgumentParser:
    """Build and return the argument parser for all CLI commands.

    Returns:
        argparse.ArgumentParser: Configured parser with all subcommands.
    """
    p = argparse.ArgumentParser(
        prog="bbl-shutter-cam",
        description="Use a BBL_SHUTTER BLE trigger to capture photos with rpicam-still.",
    )
    p.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG_PATH,
        help=f"Path to config.toml (default: {DEFAULT_CONFIG_PATH})",
    )
    p.add_argument(
        "--log-level",
        default="info",
        choices=["debug", "info", "warning", "error"],
        help="Logging verbosity",
    )
    p.add_argument(
        "--log-format",
        default="plain",
        choices=["plain", "time"],
        help="Logging format",
    )
    p.add_argument(
        "--log-file",
        default=None,
        help="Optional log file path (append mode)",
    )

    sub = p.add_subparsers(dest="command", required=True)

    # scan
    scan = sub.add_parser("scan", help="Scan for BLE devices (optionally filter by name)")
    scan.add_argument("--name", default=None, help="Device name filter (e.g. BBL_SHUTTER)")
    scan.add_argument("--timeout", type=float, default=8.0, help="Scan duration seconds")
    scan.set_defaults(func=_cmd_scan)

    # setup
    setup = sub.add_parser("setup", help="Create/update a profile and learn notify UUID by pressing the shutter")
    setup.add_argument("--profile", required=True, help="Profile name (e.g. p1s-office)")
    setup.add_argument("--name", default="BBL_SHUTTER", help="Device name to look for (default: BBL_SHUTTER)")
    setup.add_argument("--mac", default=None, help="Override: use this MAC instead of scanning")
    setup.add_argument("--timeout", type=float, default=10.0, help="Scan timeout seconds")
    setup.add_argument("--press-timeout", type=float, default=30.0, help="Seconds to wait for a shutter press")
    setup.add_argument("--verbose", action="store_true", help="Print BLE notify payloads while learning")
    setup.set_defaults(func=_cmd_setup)

    # debug
    debug = sub.add_parser("debug", help="Capture all BLE signals to discover unknown triggers and update config")
    debug.add_argument("--profile", required=True, help="Profile name (e.g. p1s-office)")
    debug.add_argument("--mac", default=None, help="Override: use this MAC instead of pulling from profile")
    debug.add_argument("--duration", type=float, default=120.0, help="Listen duration seconds (0 = infinite)")
    debug.add_argument("--update-config", action="store_true", help="Automatically update config with discovered signals")
    debug.set_defaults(func=_cmd_debug)

    # tune
    tune_cmd = sub.add_parser("tune", help="Interactive camera calibration and tuning")
    tune_cmd.add_argument("--profile", required=True, help="Profile name to tune (e.g. p1s-office)")
    tune_cmd.set_defaults(func=_cmd_tune)

    # run
    run = sub.add_parser("run", help="Run listener for a profile")
    run.add_argument("--profile", default=None, help="Profile name (default: config default_profile)")
    run.add_argument("--dry-run", action="store_true", help="Log presses but do not capture photos")
    run.add_argument("--verbose", action="store_true", help="Print BLE notification payloads")
    run.add_argument("--reconnect-delay", type=float, default=2.0, help="Seconds between reconnect attempts")
    run.set_defaults(func=_cmd_run)

    return p


def _cmd_scan(args: argparse.Namespace) -> int:
    """Scan for nearby BLE devices.

    Performs a BLE scan and prints discovered devices. Optionally filters
    results by device name.

    Args:
        args: Parsed command-line arguments containing:
            - name: Optional device name filter
            - timeout: Scan duration in seconds

    Returns:
        0 on success, 1 if no devices found.
    """
    if not devices:
        LOG.warning("No BLE devices found (or none matching).")
        return 1

    LOG.info("Found devices:")
    for d in devices:
        nm = d.name if d.name else ""
        print(f"  - name={nm!r}  mac={d.address}")
    return 0


def _cmd_setup(args: argparse.Namespace) -> int:
    """Set up a new printer profile with device pairing and signal learning.

    Interactive setup that:
    1. Scans for the BLE device (or uses provided MAC)
    2. Learns the notify UUID by waiting for a button press
    3. Saves configuration to config.toml

    Args:
        args: Parsed command-line arguments containing:
            - config: Path to config.toml
            - profile: Profile name to create/update
            - name: Device name to scan for (default: BBL_SHUTTER)
            - mac: Optional MAC address to skip scanning
            - timeout: Scan timeout in seconds
            - press_timeout: Time to wait for button press in seconds
            - verbose: Whether to print BLE payloads during learning

    Returns:
        0 on success, 1 on failure.
    """

    result = asyncio.run(
        discover.setup_profile(
            config_path=cfg_path,
            profile=args.profile,
            device_name=args.name,
            mac=args.mac,
            scan_timeout=args.timeout,
            press_timeout=args.press_timeout,
            verbose=args.verbose,
        )
    )

    if not result:
        return 1

    mac, notify_uuid = result
    LOG.info(f"Setup complete for profile '{args.profile}'")
    print(f"    MAC: {mac}")
    print(f"    notify_uuid: {notify_uuid}")
    print()
    LOG.info("Next: dry run")
    print(f"    bbl-shutter-cam run --profile {args.profile} --dry-run --verbose")
    LOG.info("Then: run for real")
    print(f"    bbl-shutter-cam run --profile {args.profile}")
    return 0


def _cmd_debug(args: argparse.Namespace) -> int:
    """Discover and log unknown BLE signals from a device.

    Connects to a device and listens for all BLE notifications, logging
    their hex values. Useful for discovering new trigger signals or
    debugging connection issues.

    Args:
        args: Parsed command-line arguments containing:
            - config: Path to config.toml
            - profile: Profile name to use
            - mac: Optional MAC address (overrides profile config)
            - duration: Listen duration in seconds (0 = infinite)
            - update_config: Whether to auto-save discovered signals

    Returns:
        0 on success, 1 on failure.
    """

    prof = load_profile(cfg_path, args.profile)
    mac = args.mac or prof.get("device", {}).get("mac")

    if not mac:
        LOG.error(f"Profile '{args.profile}' has no MAC. Run setup first or provide --mac.")
        return 1

    asyncio.run(
        discover.debug_signals(
            config_path=cfg_path,
            profile_name=args.profile,
            mac=mac,
            duration=args.duration,
            update_config=args.update_config,
        )
    )
    return 0


def _cmd_tune(args: argparse.Namespace) -> int:
    """Interactive camera tuning for a profile.

    Launches an interactive menu for adjusting camera settings
    (focus, exposure, color, etc.) with live test photo capture.

    Args:
        args: Parsed command-line arguments containing:
            - config: Path to config.toml
            - profile: Profile name to tune

    Returns:
        0 on success, 1 on failure.
    """
    cfg_path = Path(args.config).expanduser()
    ensure_config_exists(cfg_path)

    return tune.tune_profile(cfg_path, args.profile)


def _cmd_run(args: argparse.Namespace) -> int:
    """Listen for shutter signals and capture photos.

    Main operation mode. Connects to a configured BLE device and listens
    for trigger signals. On each trigger, captures a photo using rpicam-still
    with settings from the profile configuration.

    Auto-reconnects on connection loss. Use Ctrl+C to stop.

    Args:
        args: Parsed command-line arguments containing:
            - config: Path to config.toml
            - profile: Profile name to use (or default_profile from config)
            - dry_run: If True, logs triggers but doesn't capture photos
            - verbose: Whether to print BLE notification payloads
            - reconnect_delay: Seconds between reconnection attempts

    Returns:
        0 on normal exit, 1 on error (typically not reached due to Ctrl+C).
    """

    prof = load_profile(cfg_path, args.profile)
    asyncio.run(
        discover.run_profile(
            prof,
            dry_run=args.dry_run,
            verbose=args.verbose,
            reconnect_delay=args.reconnect_delay,
        )
    )
    return 0


def main(argv: list[str] | None = None) -> None:
    """Entry point for the CLI application.

    Parses arguments, initializes logging, and dispatches to the appropriate
    command handler (scan, setup, debug, or run).

    Args:
        argv: List of command-line arguments (defaults to sys.argv[1:])

    Raises:
        SystemExit: With exit code 0 on success, 1 on error, 2 on bad arguments.
    """
    parser = _build_parser()
    args = parser.parse_args(argv)

    # Initialize logging early
    configure_logging(
        level=args.log_level,
        fmt=args.log_format,
        log_file=args.log_file,
    )
    LOG.debug(f"Using config: {args.config}")

    func = getattr(args, "func", None)
    if not func:
        parser.print_help()
        raise SystemExit(2)

    rc = func(args)
    raise SystemExit(rc)


if __name__ == "__main__":
    main(sys.argv[1:])
