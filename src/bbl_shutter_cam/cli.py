# src/bbl_shutter_cam/cli.py
from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

from . import discover
from .config import DEFAULT_CONFIG_PATH, ensure_config_exists, load_profile
from .util import LOG, configure_logging


def _build_parser() -> argparse.ArgumentParser:
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

    # run
    run = sub.add_parser("run", help="Run listener for a profile")
    run.add_argument("--profile", default=None, help="Profile name (default: config default_profile)")
    run.add_argument("--dry-run", action="store_true", help="Log presses but do not capture photos")
    run.add_argument("--verbose", action="store_true", help="Print BLE notification payloads")
    run.add_argument("--reconnect-delay", type=float, default=2.0, help="Seconds between reconnect attempts")
    run.set_defaults(func=_cmd_run)

    return p


def _cmd_scan(args: argparse.Namespace) -> int:
    devices = asyncio.run(discover.scan(name_filter=args.name, timeout=args.timeout))
    if not devices:
        LOG.warning("No BLE devices found (or none matching).")
        return 1

    LOG.info("Found devices:")
    for d in devices:
        nm = d.name if d.name else ""
        print(f"  - name={nm!r}  mac={d.address}")
    return 0


def _cmd_setup(args: argparse.Namespace) -> int:
    cfg_path: Path = args.config
    ensure_config_exists(cfg_path)

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


def _cmd_run(args: argparse.Namespace) -> int:
    cfg_path: Path = args.config
    ensure_config_exists(cfg_path)

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
