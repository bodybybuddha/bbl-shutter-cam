"""Device discovery and orchestration of photo capture.

High-level functions for:
    - BLE device scanning and filtering
    - Interactive device pairing (learning notify UUID)
    - Profile setup and configuration
    - Main event loop for photo capture on shutter signals

This module bridges configuration, BLE, and camera modules to provide the
core photo capture functionality.
"""
from __future__ import annotations

import asyncio
import subprocess
from typing import Any, Dict, Optional, Tuple

from bleak import BleakScanner

from . import ble
from .camera import build_rpicam_still_cmd, camera_config_from_profile, make_outfile
from .config import update_profile_device_fields
from .util import LOG

# Default press bytes for notify UUID learning.
PRESS_BYTES = b"\x40\x00"  # Manual button press


async def scan(name_filter: Optional[str] = None, timeout: float = 8.0):
    """Scan for nearby BLE devices.

    Performs a BLE scan and optionally filters results by device name.

    Args:
        name_filter: Optional device name to filter by (exact match); if None,
                    returns all discovered devices
        timeout: Scan duration in seconds

    Returns:
        List of BleakDevice objects discovered

    Example:
        >>> devices = await scan(name_filter="BBL_SHUTTER", timeout=10)
        >>> for dev in devices:
        ...     print(f"{dev.name} ({dev.address})")
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
    """Interactively learn which characteristic sends shutter button signals.

    Connects to a device, subscribes to all notify characteristics, and waits
    for a button press event. Returns the UUID of the characteristic that
    produced the signal.

    Args:
        mac: Device MAC address (e.g., "AA:BB:CC:DD:EE:FF")
        press_timeout: Seconds to wait for a button press before timing out
        verbose: Whether to print all received notifications while waiting

    Returns:
        UUID of the characteristic that sent the button press signal

    Raises:
        RuntimeError: If no notify characteristics found or subscription fails
        asyncio.TimeoutError: If no signal is received within press_timeout

    Example:
        >>> uuid = await learn_notify_uuid("AA:BB:CC:DD:EE:FF", press_timeout=30)
        >>> print(f"Press signal comes from UUID: {uuid}")

    Note:
        The device must send the button press while this function is running.
        Takes approximately 2-5 seconds to connect and discover characteristics.
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

        LOG.info(
            f"Learning notify UUID: press the shutter button now (timeout {int(press_timeout)}s)…"
        )
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
    """Complete interactive setup for a new or existing profile.

    High-level setup that:
    1. Scans for the device by name (or uses provided MAC)
    2. Learns the notify UUID by waiting for a button press
    3. Writes configuration to config.toml

    Args:
        config_path: Path to config.toml file
        profile: Profile name to create/update
        device_name: BLE device name to scan for (default: "BBL_SHUTTER")
        mac: Optional MAC address to skip scanning
        scan_timeout: BLE scan timeout in seconds
        press_timeout: Time to wait for button press in seconds
        verbose: Print BLE notifications while learning

    Returns:
        Tuple of (mac, notify_uuid) on success, None on failure

    Example:
        >>> result = await setup_profile(config_path, "office")
        >>> if result:
        ...     mac, uuid = result
        ...     print(f"Setup complete: {mac} -> {uuid}")
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
    """Main event loop: listen for shutter signals and capture photos.

    Connects to the BLE device from the profile and listens for configured
    trigger events. On each trigger, captures a photo using rpicam-still with
    settings from the profile. Automatically reconnects on connection loss.

    Args:
        profile: Profile dict (from load_profile()) containing:
            - device.mac: Device MAC address
            - device.notify_uuid: Characteristic UUID for signals
            - device.events: List of trigger events with hex and capture flags
            - camera: Camera settings for rpicam-still
        dry_run: If True, log triggers but don't actually capture photos
        verbose: Print BLE notification payloads as received
        reconnect_delay: Seconds between reconnection attempts

    Raises:
        SystemExit: If profile is missing required fields (MAC, notify_uuid)

    Note:
        This function runs indefinitely. Press Ctrl+C to stop.
        Will automatically reconnect if the device disconnects.

    Example:
        >>> prof = load_profile(config_path, "office")
        >>> await run_profile(prof, dry_run=False, verbose=True)
        >>> # Listens for shutter signals and captures photos...
    """
    from .config import get_trigger_events

    dev = profile.get("device", {}) or {}
    mac = dev.get("mac")
    notify_uuid = dev.get("notify_uuid")

    if not mac:
        raise SystemExit(
            "[!] Profile has no device.mac. Run: bbl-shutter-cam setup --profile <name>"
        )
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

            await client.start_notify(notify_uuid, on_notify)  # type: ignore[arg-type]
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
    """Listen for all BLE signals and log them for analysis.

    Connects to a device and captures all BLE notifications, printing each one
    with hex, decimal, and length information. Useful for discovering new trigger
    signals or debugging connection issues.

    Optionally updates the profile configuration with discovered signals
    automatically.

    Args:
        config_path: Path to config.toml file
        profile_name: Profile name to optionally update with discovered signals
        mac: Device MAC address to connect to
        duration: Listen duration in seconds (0 = listen indefinitely)
        update_config: If True, automatically save discovered signals to config

    Output Format (for each signal received):
        [HH:MM:SS.mmm] <UUID>
                   HEX: <uppercase hex string>
                   DEC: <space-separated decimal values>
                   LEN: <number of bytes>

    Final Summary:
        - Lists each UUID
        - Shows unique signals from that UUID with receive count
        - Updates config if requested

    Example:
        >>> await debug_signals(
        ...     Path("~/.config/bbl-shutter-cam/config.toml"),
        ...     "office",
        ...     "AA:BB:CC:DD:EE:FF",
        ...     duration=120,
        ...     update_config=True
        ... )
        >>> # Listens for 120 seconds, captures all signals, updates config
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
        seen_data: dict[str, set[bytes]] = {}

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
    """Update profile configuration with discovered BLE signals.

    Takes the signals captured by debug_signals() and writes them to the
    profile's device.events section in config.toml. Automatically marks
    all signals except "0000" (release) for photo capture.

    Args:
        config_path: Path to config.toml file
        profile_name: Profile name to update
        seen_data: Dict mapping UUID -> list of signal bytes objects
                  (typically from debug_signals())

    Notes:
        - Signal "0000" is automatically marked as non-capturing (release event)
        - Other signals are marked for capture by default
        - Includes signal frequency count in config for reference
        - Logs success/failure via LOG

    Raises:
        No exceptions; errors are logged and printed to user
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
                events.append(
                    {
                        "uuid": uuid,
                        "hex": hex_sig,
                        "count": count,
                        "capture": should_capture,
                    }
                )

        prof["device"]["events"] = events
        save_config(cfg, config_path)

        LOG.info(f"Updated profile '{profile_name}' with {len(events)} discovered signal(s)")
        print(f"\n✓ Config updated with {len(events)} signal(s)")
        print(f"  Location: {config_path}")

    except Exception as e:
        LOG.error(f"Failed to update config: {e}")
