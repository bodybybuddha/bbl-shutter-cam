# src/bbl_shutter_cam/ble.py
from __future__ import annotations

import asyncio
from typing import Callable, Iterable, List

from bleak import BleakClient

from .util import LOG

NotifyCallback = Callable[[int, bytearray], None]


async def connect_with_retry(mac: str, reconnect_delay: float = 2.0) -> BleakClient:
    """
    Attempt to connect to a BLE MAC address until successful.
    Battery devices may only connect when awake (e.g. after a button press).
    """
    while True:
        try:
            client = BleakClient(mac)
            await client.connect()
            if client.is_connected:
                LOG.debug(f"BLE connected: {mac}")
                return client
        except Exception as e:
            LOG.debug(f"BLE connect failed ({mac}): {e.__class__.__name__}: {e}")
        await asyncio.sleep(reconnect_delay)


async def get_services_compat(client: BleakClient):
    """
    Bleak API compatibility helper:
    - Some versions use await client.get_services()
    - Others populate client.services asynchronously
    """
    if hasattr(client, "get_services"):
        gs = getattr(client, "get_services")
        if asyncio.iscoroutinefunction(gs):
            return await gs()
        return gs()

    for _ in range(25):
        services = getattr(client, "services", None)
        if services:
            return services
        await asyncio.sleep(0.2)

    raise RuntimeError("Service discovery failed: BleakClient.services never populated.")


async def list_notify_characteristics(client: BleakClient) -> List[str]:
    """
    Return UUIDs for all characteristics that advertise 'notify'.
    """
    services = await get_services_compat(client)
    notify_uuids: List[str] = []

    for svc in services:
        for ch in svc.characteristics:
            props = set(getattr(ch, "properties", []) or [])
            if "notify" in props:
                notify_uuids.append(ch.uuid)

    LOG.debug(f"Found {len(notify_uuids)} notify characteristic(s)")
    return notify_uuids


async def start_notify_best_effort(
    client: BleakClient,
    uuids: Iterable[str],
    callback_factory: Callable[[str], NotifyCallback],
) -> List[str]:
    """
    Attempt to start notifications on a list of UUIDs.
    Returns the UUIDs that successfully subscribed.
    """
    active: List[str] = []
    for uuid in uuids:
        try:
            await client.start_notify(uuid, callback_factory(uuid))
            active.append(uuid)
        except Exception as e:
            LOG.debug(f"start_notify failed for {uuid}: {e.__class__.__name__}: {e}")
            continue
    return active


async def stop_notify_best_effort(client: BleakClient, uuids: Iterable[str]) -> None:
    """
    Best-effort stop notifications for UUIDs. Failures are ignored.
    """
    for uuid in uuids:
        try:
            await client.stop_notify(uuid)
        except Exception:
            pass
