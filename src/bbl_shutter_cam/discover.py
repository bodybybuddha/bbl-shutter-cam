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

PRESS_BYTES = b"\x40\x00"
RELEASE_BYTES = b"\x00\x00"


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
    Connect + subscribe to notify_uuid and trigger rpicam-still on press.
    Auto-reconnects and re-subscribes.
    """
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

    prof_name = profile.get("_profile_name", "unknown")
    LOG.info(f"Profile: {prof_name}")
    LOG.info(f"MAC: {mac}")
    LOG.info(f"Notify UUID: {notify_uuid}")
    LOG.info(f"Output dir: {cam_cfg.output_dir}")
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

                if b == PRESS_BYTES:
                    now = asyncio.get_event_loop().time()
                    if now - last_press < min_interval:
                        LOG.debug("Debounced press (too soon).")
                        return
                    last_press = now

                    LOG.info("SHUTTER PRESS (4000)")
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

                elif b == RELEASE_BYTES:
                    LOG.debug("Release (0000)")

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
            await asyncio.sleep(reconnect_delay)
