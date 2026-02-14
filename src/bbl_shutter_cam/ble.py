"""Bluetooth Low Energy (BLE) utilities and abstractions.

Provides low-level BLE device operations using the Bleak library:
    - Async connection with automatic retry
    - Service and characteristic discovery
    - Notification subscription with error handling
    - Cross-version Bleak API compatibility

All operations are async/await and non-blocking.
"""
from __future__ import annotations

import asyncio
from typing import Callable, Iterable, List

from bleak import BleakClient

from .util import LOG

# Type alias for BLE notification callbacks
NotifyCallback = Callable[[int, bytearray], None]


async def connect_with_retry(mac: str, reconnect_delay: float = 2.0) -> BleakClient:
    """Connect to a BLE device with automatic retry on failure.

    Loops indefinitely attempting connection, waiting reconnect_delay seconds
    between attempts. Useful for battery-powered devices that may only respond
    when awake (e.g., after a button press).

    Args:
        mac: MAC address of device (e.g., "AA:BB:CC:DD:EE:FF")
        reconnect_delay: Seconds to wait between connection attempts

    Returns:
        BleakClient: Connected client instance (is_connected == True)

    Note:
        This function blocks indefinitely if the device is not available.
        The caller should implement a timeout if needed.
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
    """Discover services from a BLE client (handles Bleak version differences).

    Some versions of Bleak expose services via await client.get_services(),
    while others populate client.services asynchronously. This helper handles
    both patterns transparently.

    Args:
        client: Connected BleakClient instance

    Returns:
        Services structure (GattServices collection)

    Raises:
        RuntimeError: If service discovery fails (timeout or unsupported Bleak version)
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
    """List UUIDs of all characteristics that support notifications.

    Discovers all services and their characteristics, filtering to those
    with the "notify" property set.

    Args:
        client: Connected BleakClient instance

    Returns:
        List[str]: UUIDs of notifiable characteristics

    Example:
        >>> client = await connect_with_retry("AA:BB:CC:DD:EE:FF")
        >>> uuids = await list_notify_characteristics(client)
        >>> for uuid in uuids:
        >>>     print(uuid)
        180a0000-0000-1000-8000-00805f9b34fb
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
    """Subscribe to notifications on multiple characteristics with error tolerance.

    Attempts to subscribe to each UUID, silently skipping any that fail.
    Uses a callback_factory that receives the UUID and returns a callback function
    to handle notifications.

    Args:
        client: Connected BleakClient instance
        uuids: Iterable of characteristic UUIDs to subscribe to
        callback_factory: Function that takes a UUID string and returns a NotifyCallback
                         (function with signature: callback(sender: int, data: bytearray))

    Returns:
        List[str]: UUIDs that successfully subscribed

    Example:
        >>> def create_callback(uuid):
        ...     def callback(sender, data):
        ...         print(f"Notification from UUID {uuid}: {data.hex()}")
        ...     return callback
        >>> active = await start_notify_best_effort(client, uuids, create_callback)
        >>> print(f"Subscribed to {len(active)} characteristics")
    """
    active: List[str] = []
    for uuid in uuids:
        try:
            await client.start_notify(uuid, callback_factory(uuid))  # type: ignore[arg-type]
            active.append(uuid)
        except Exception as e:
            LOG.debug(f"start_notify failed for {uuid}: {e.__class__.__name__}: {e}")
            continue
    return active


async def stop_notify_best_effort(client: BleakClient, uuids: Iterable[str]) -> None:
    """Unsubscribe from notifications with error tolerance.

    Attempts to stop notifications on each UUID. Failures are silently ignored,
    making this safe to call even if some subscriptions were never established.

    Args:
        client: Connected BleakClient instance
        uuids: Iterable of characteristic UUIDs to unsubscribe from

    Example:
        >>> await stop_notify_best_effort(client, ["uuid1", "uuid2"])
        >>> # Client no longer receives notifications
    """
    for uuid in uuids:
        try:
            await client.stop_notify(uuid)
        except Exception:
            pass
