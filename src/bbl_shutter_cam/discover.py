# src/bbl_shutter_cam/discover.py
from __future__ import annotations

import asyncio
import subprocess
from typing import Any, Dict, Optional, Tuple

from bleak import BleakScanner

from . import ble
from .camera import build_rpicam_still_cmd, camera_config_from_profile, make_outfile
from .config import update_profile_device_fields
from .util import LOG

# Deprecated: Use dynamically loaded events from config instead.
# Kept for reference / backward compatibility only.
# PRESS_BYTES = b"\x40\x00"              # Manual button press
# BAMBU_STUDIO_TRIGGER = b"\x80\x00"      # Bambu Studio app trigger
# RELEASE_BYTES = b"\x00\x00"



async def scan(name_filter: Optional[str] = None, timeout: float = 8.0):
    """
    Scan for BLE devices. If name_filter is provided, only return devices matching exactly.
    """
    LOG.debug(f"BLE scan start: timeout={timeout}s filter={name_filter!r}")
    devices = await BleakScanner.discover(timeout=timeout)

    if not name_filter:
        LOG.debug(f"BLE scan done: {len(devices)} device(s) found")
        return devices

    hits = []
    for d in devices:
        if (d.name or "").strip() == name_filter:
            hits.append(d)

    LOG.debug(f"BLE scan done: {len(hits)} matching device(s) found")
    return hits


async def learn_notify_uuid(mac: str, press_timeout: float = 30.0, verbose: bool = False) -> str:
    """
    Connect to device, subscribe to all NOTIFY characteristics, then wait for 0x4000 (press).
    Returns the UUID that produced the press event.
    """
    LOG.info(f"Connecting to shutter @ {mac} (may require waking the device)…")
    client = await ble.connect_with_retry(mac)
    try:
        LOG.debug("Connected. Discovering NOTIFY characteristics…")
        notify_uuids = await ble.list_notify_characteristics(client)
        LOG.debug(f"Notify characteristics discovered: {len(notify_uuids)}")

        if not notify_uuids:
            raise RuntimeError("No notify characteristics found to learn from.")

        loop = asyncio.get_event_loop()
        found: asyncio.Future[str] = loop.create_future()

        def cb_factory(uuid: str):
            def _cb(_sender: int, data: bytearray):
                b = bytes(data)
                if verbose:
                    print(f"[notify:{uuid}] {b.hex()}")
                if b == PRESS_BYTES and not found.done():
                    found.set_result(uuid)

            return _cb

        active = await ble.start_notify_best_effort(client, notify_uuids, cb_factory)
        LOG.debug(f"Subscribed to {len(active)}/{len(notify_uuids)} notify characteristic(s)")

        if not active:
            raise RuntimeError("Could not subscribe to any notify characteristics.")

        LOG.info(f"Learning notify UUID: press the shutter button now (timeout {int(press_timeout)}s)…")
        try:
            uuid = await asyncio.wait_for(found, timeout=press_timeout)
            LOG.info(f"Learned notify UUID: {uuid}")
            return uuid
        finally:
            await ble.stop_notify_best_effort(client, active)
    finally:
        try:
            await client.disconnect()
        except Exception:
            pass


async def setup_profile(
    config_path,
    profile: str,
    device_name: str = "BBL_SHUTTER",
    mac: Optional[str] = None,
    scan_timeout: float = 10.0,
    press_timeout: float = 30.0,
    verbose: bool = False,
) -> Optional[Tuple[str, str]]:
    """
    High-level setup:
      - Scan/find device by name (or use provided MAC)
      - Learn notify UUID by waiting for a press event
      - Write mac + notify_uuid into config for the profile
    Returns (mac, notify_uuid) or None on failure.
    """
    if not mac:
        LOG.info(f"Scanning for BLE device named {device_name!r}…")
        hits = await scan(name_filter=device_name, timeout=scan_timeout)
        if not hits:
            LOG.error("No matching devices found. Try again, increase timeout, or provide --mac.")
            return None
        mac = hits[0].address
        LOG.info(f"Found {device_name} @ {mac}")

    notify_uuid = await learn_notify_uuid(mac, press_timeout=press_timeout, verbose=verbose)
    update_profile_device_fields(config_path, profile, mac, notify_uuid)
    LOG.info(f"Wrote MAC + notify_uuid to profile '{profile}'")
    return (mac, notify_uuid)


async def run_profile(
    profile: Dict[str, Any],
    dry_run: bool = False,
    verbose: bool = False,
    reconnect_delay: float = 2.0,
) -> None:
    """
    Connect + subscribe to notify_uuid and trigger rpicam-still on configured events.
    Auto-reconnects and re-subscribes.
    Uses dynamic trigger events from profile config.
    """
    from .config import get_trigger_events

    dev = profile.get("device", {}) or {}
    mac = dev.get("mac")
    notify_uuid = dev.get("notify_uuid")

    if not mac:
        raise SystemExit("[!] Profile has no device.mac. Run: bbl-shutter-cam setup --profile <name>")
    if not notify_uuid:
        raise SystemExit("[!] Profile has no device.notify_uuid. Run setup to learn it.")

    cam_cfg = camera_config_from_profile(profile)
    min_interval = cam_cfg.min_interval_sec
    last_press = 0.0

    # Load trigger events from config
    trigger_events = get_trigger_events(profile)
    trigger_map = {}  # Maps bytes -> event info
    for event in trigger_events:
        if event.get("capture", False):
            try:
                hex_str = event.get("hex", "")
                trigger_bytes = bytes.fromhex(hex_str)
                trigger_map[trigger_bytes] = event
            except ValueError:
                pass

    prof_name = profile.get("_profile_name", "unknown")
    LOG.info(f"Profile: {prof_name}")
    LOG.info(f"MAC: {mac}")
    LOG.info(f"Notify UUID: {notify_uuid}")
    LOG.info(f"Output dir: {cam_cfg.output_dir}")
    LOG.info(f"Configured triggers: {len(trigger_map)}")
    if dry_run:
        LOG.warning("Dry-run enabled: no photos will be taken.")

    while True:
        client = None
        try:
            LOG.info("Connecting…")
            client = await ble.connect_with_retry(mac, reconnect_delay=reconnect_delay)
            LOG.info("Connected; subscribing to notifications…")

            def on_notify(_sender: int, data: bytearray):
                nonlocal last_press
                b = bytes(data)

                if verbose:
                    print(f"[notify] {b.hex()}")

                # Check if this is a configured trigger event
                if b in trigger_map:
                    now = asyncio.get_event_loop().time()
                    if now - last_press < min_interval:
                        LOG.debug("Debounced press (too soon).")
                        return
                    last_press = now

                    event = trigger_map[b]
                    event_name = event.get("name", b.hex())
                    LOG.info(f"SHUTTER PRESS ({event_name}) {b.hex()}")
                    if dry_run:
                        return

                    outfile = make_outfile(cam_cfg)
                    cmd = build_rpicam_still_cmd(cam_cfg, outfile)
                    LOG.debug(f"Capture cmd: {' '.join(cmd)}")

                    try:
                        subprocess.run(cmd, check=True)
                        LOG.info(f"Captured: {outfile}")
                    except subprocess.CalledProcessError as e:
                        LOG.error(f"rpicam-still failed: {e}")

            await client.start_notify(notify_uuid, on_notify)
            LOG.info("Listening… (Ctrl+C to quit)")

            while client.is_connected:
                await asyncio.sleep(0.5)

            LOG.warning("Disconnected; will reconnect…")
        except KeyboardInterrupt:
            LOG.info("Exiting.")
            return
        except Exception as e:
            LOG.error(f"{e.__class__.__name__}: {e}")
        finally:
            if client:
                try:
                    await client.disconnect()
                except Exception:
                    pass


async def debug_signals(
    config_path,
    profile_name: str,
    mac: str,
    duration: float = 120.0,
    update_config: bool = False,
) -> None:
    """
    Connect to device and capture all BLE notification signals for analysis.
    Optionally update the profile config with discovered signals.
    """
    from datetime import datetime

    LOG.info(f"Connecting to {mac}…")
    client = await ble.connect_with_retry(mac)

    try:
        LOG.info("Connected. Discovering NOTIFY characteristics…")
        notify_uuids = await ble.list_notify_characteristics(client)
        LOG.info(f"Found {len(notify_uuids)} NOTIFY characteristic(s):")
        for uuid in notify_uuids:
            print(f"  - {uuid}")
        print()

        if not notify_uuids:
            LOG.error("No NOTIFY characteristics found.")
            return

        # Track signals by UUID
        seen_data = {}

        def make_callback(uuid: str):
            def callback(_sender: int, data: bytearray) -> None:
                b = bytes(data)
                timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]

                if uuid not in seen_data:
                    seen_data[uuid] = []
                seen_data[uuid].append(b)

                hex_str = b.hex().upper()
                dec_values = " ".join(f"{byte:3d}" for byte in b)
                print(f"[{timestamp}] {uuid}")
                print(f"           HEX: {hex_str}")
                print(f"           DEC: {dec_values}")
                print(f"           LEN: {len(b)} bytes")
                print()

            return callback

        # Subscribe to all
        LOG.info("Subscribing to all NOTIFY characteristics…")
        active = []
        for uuid in notify_uuids:
            try:
                await client.start_notify(uuid, make_callback(uuid))
                active.append(uuid)
            except Exception as e:
                LOG.warning(f"Failed to subscribe to {uuid}: {e}")

        LOG.info(f"Successfully subscribed to {len(active)}/{len(notify_uuids)} characteristics")
        print()

        if duration > 0:
            print(f"Listening for {int(duration)} seconds…")
            print("(Trigger your device now to see signals)")
            print()
            await asyncio.sleep(duration)
        else:
            print("Listening indefinitely… Press Ctrl+C to exit")
            print()
            try:
                while client.is_connected:
                    await asyncio.sleep(1)
            except (KeyboardInterrupt, asyncio.CancelledError):
                print("\nStopping capture…")

        # Print summary
        print("\n" + "=" * 60)
        print("SIGNAL SUMMARY")
        print("=" * 60)
        for uuid in sorted(seen_data.keys()):
            signals = seen_data[uuid]
            unique_signals = {}
            for sig in signals:
                hex_sig = sig.hex().upper()
                if hex_sig not in unique_signals:
                    unique_signals[hex_sig] = 0
                unique_signals[hex_sig] += 1

            print(f"\n{uuid}:")
            for hex_sig, count in sorted(unique_signals.items(), key=lambda x: -x[1]):
                print(f"  {hex_sig:20s} (received {count} time(s))")

        # Update config if requested
        if update_config and seen_data:
            _update_config_with_signals(config_path, profile_name, seen_data)

    finally:
        try:
            await client.disconnect()
        except Exception:
            pass


def _update_config_with_signals(
    config_path,
    profile_name: str,
    seen_data: Dict[str, list],
) -> None:
    """
    Update profile config with discovered signals.
    """
    from .config import load_config, save_config

    try:
        cfg = load_config(config_path)
        prof = cfg.get("profiles", {}).get(profile_name)

        if not prof:
            LOG.error(f"Profile '{profile_name}' not found in config.")
            return

        # Initialize device section if needed
        if "device" not in prof:
            prof["device"] = {}

        # Create events section
        if "events" not in prof["device"]:
            prof["device"]["events"] = []

        # Build event list from discovered signals
        events = []
        for uuid in sorted(seen_data.keys()):
            signals = seen_data[uuid]
            unique_signals = {}
            for sig in signals:
                hex_sig = sig.hex().upper()
                if hex_sig not in unique_signals:
                    unique_signals[hex_sig] = 0
                unique_signals[hex_sig] += 1

            for hex_sig, count in sorted(unique_signals.items(), key=lambda x: -x[1]):
                # Skip release signals by default
                should_capture = hex_sig != "0000"
                events.append({
                    "uuid": uuid,
                    "hex": hex_sig,
                    "count": count,
                    "capture": should_capture,
                })

        prof["device"]["events"] = events
        save_config(cfg, config_path)

        LOG.info(f"Updated profile '{profile_name}' with {len(events)} discovered signal(s)")
        print(f"\n✓ Config updated with {len(events)} signal(s)")
        print(f"  Location: {config_path}")

    except Exception as e:
        LOG.error(f"Failed to update config: {e}")

