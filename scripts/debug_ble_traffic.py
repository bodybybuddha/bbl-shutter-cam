#!/usr/bin/env python3
"""
Debug utility: Subscribe to all BLE traffic from a configured device.

This script connects to a Bambu Lab cyberbrick and captures ALL notification
signals to help identify the correct trigger signal format.

Usage:
    python3 scripts/debug_ble_traffic.py --profile ps1-office
    python3 scripts/debug_ble_traffic.py --mac B8:F8:62:A9:92:7E
"""

import argparse
import asyncio
import sys
from datetime import datetime
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from bleak import BleakClient
from bbl_shutter_cam.config import DEFAULT_CONFIG_PATH, load_profile
from bbl_shutter_cam.ble import connect_with_retry, list_notify_characteristics
from bbl_shutter_cam.util import configure_logging, LOG


async def debug_ble_traffic(mac: str, duration: float = 120.0):
    """
    Connect to device and print all BLE notification traffic.
    
    Args:
        mac: MAC address of the device
        duration: How long to listen (seconds). 0 = infinite.
    """
    LOG.info(f"Connecting to {mac}…")
    client = await connect_with_retry(mac)
    
    try:
        LOG.info("Connected. Discovering NOTIFY characteristics…")
        notify_uuids = await list_notify_characteristics(client)
        LOG.info(f"Found {len(notify_uuids)} NOTIFY characteristic(s):")
        for uuid in notify_uuids:
            print(f"  - {uuid}")
        print()
        
        if not notify_uuids:
            LOG.error("No NOTIFY characteristics found.")
            return
        
        # Track which UUIDs have data
        seen_data = {}
        
        def make_callback(uuid: str):
            def callback(_sender: int, data: bytearray) -> None:
                b = bytes(data)
                timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                
                # Track this UUID
                if uuid not in seen_data:
                    seen_data[uuid] = []
                seen_data[uuid].append(b)
                
                # Print in human-readable format
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
            print("(Trigger your device now to see the signals)")
            print()
            await asyncio.sleep(duration)
        else:
            print("Listening indefinitely…")
            print("Press Ctrl+C to exit")
            print()
            try:
                while client.is_connected:
                    await asyncio.sleep(1)
            except (KeyboardInterrupt, asyncio.CancelledError):
                print("\nExiting…")
        
        # Summary
        if seen_data:
            print("\n" + "="*60)
            print("SUMMARY OF OBSERVED SIGNALS")
            print("="*60)
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
        else:
            print("\nNo signals received.")
    
    finally:
        try:
            await client.disconnect()
        except Exception:
            pass


async def main():
    parser = argparse.ArgumentParser(
        description="Capture all BLE notification traffic from a device"
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG_PATH,
        help=f"Path to config.toml (default: {DEFAULT_CONFIG_PATH})",
    )
    parser.add_argument(
        "--profile",
        default=None,
        help="Profile name from config (e.g. ps1-office)",
    )
    parser.add_argument(
        "--mac",
        default=None,
        help="Device MAC address (overrides profile)",
    )
    parser.add_argument(
        "--duration",
        type=float,
        default=120.0,
        help="Listening duration in seconds (default: 120, use 0 for infinite)",
    )
    parser.add_argument(
        "--log-level",
        default="info",
        choices=["debug", "info", "warning", "error"],
        help="Logging level",
    )
    
    args = parser.parse_args()
    
    configure_logging(level=args.log_level, fmt="time")
    
    # Determine MAC address
    mac = args.mac
    if not mac:
        if not args.profile:
            parser.error("Must specify --profile or --mac")
        
        prof = load_profile(args.config, args.profile)
        mac = prof.get("device", {}).get("mac")
        if not mac:
            LOG.error(f"Profile '{args.profile}' has no MAC address. Run setup first.")
            return 1
        LOG.info(f"Using MAC from profile '{args.profile}': {mac}")
    
    try:
        await debug_ble_traffic(mac, duration=args.duration)
        return 0
    except KeyboardInterrupt:
        return 0
    except Exception as e:
        LOG.error(f"{e.__class__.__name__}: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
