"""Unit tests for ble.py module."""
import asyncio

import pytest

from bbl_shutter_cam import ble


class FakeBleakClient:
    def __init__(self, mac: str, should_connect: bool = True):
        self.mac = mac
        self.is_connected = False
        self._should_connect = should_connect
        self._start_notify_calls = []
        self._stop_notify_calls = []

    async def connect(self):
        if not self._should_connect:
            raise RuntimeError("connect failed")
        self.is_connected = True

    async def start_notify(self, uuid, _cb):
        self._start_notify_calls.append(uuid)
        if "bad" in uuid:
            raise RuntimeError("notify failed")

    async def stop_notify(self, uuid):
        self._stop_notify_calls.append(uuid)
        if "bad" in uuid:
            raise RuntimeError("stop failed")


class FakeService:
    def __init__(self, characteristics):
        self.characteristics = characteristics


class FakeChar:
    def __init__(self, uuid, properties):
        self.uuid = uuid
        self.properties = properties


def test_connect_with_retry_success(monkeypatch):
    def fake_client(mac):
        return FakeBleakClient(mac, should_connect=True)

    monkeypatch.setattr(ble, "BleakClient", fake_client)

    client = asyncio.run(ble.connect_with_retry("AA:BB"))
    assert client.is_connected is True


def test_connect_with_retry_retries(monkeypatch):
    calls = {"count": 0}

    def fake_client(mac):
        calls["count"] += 1
        should_connect = calls["count"] > 1
        return FakeBleakClient(mac, should_connect=should_connect)

    async def fake_sleep(_delay):
        return None

    monkeypatch.setattr(ble, "BleakClient", fake_client)
    monkeypatch.setattr(ble.asyncio, "sleep", fake_sleep)

    client = asyncio.run(ble.connect_with_retry("AA:BB", reconnect_delay=0.01))
    assert client.is_connected is True
    assert calls["count"] >= 2


def test_get_services_compat_with_get_services_coroutine():
    class Client:
        async def get_services(self):
            return ["service-1"]

    services = asyncio.run(ble.get_services_compat(Client()))
    assert services == ["service-1"]


def test_get_services_compat_with_get_services_function():
    class Client:
        def get_services(self):
            return ["service-2"]

    services = asyncio.run(ble.get_services_compat(Client()))
    assert services == ["service-2"]


def test_get_services_compat_with_services_attr(monkeypatch):
    class Client:
        def __init__(self):
            self.services = ["svc"]

    services = asyncio.run(ble.get_services_compat(Client()))
    assert services == ["svc"]


def test_get_services_compat_timeout(monkeypatch):
    class Client:
        services = None

    async def fake_sleep(_delay):
        return None

    monkeypatch.setattr(ble.asyncio, "sleep", fake_sleep)

    with pytest.raises(RuntimeError, match="Service discovery failed"):
        asyncio.run(ble.get_services_compat(Client()))


def test_list_notify_characteristics(monkeypatch):
    async def fake_get_services(_client):
        chars = [
            FakeChar("uuid-1", ["notify"]),
            FakeChar("uuid-2", ["read"]),
            FakeChar("uuid-3", ["notify", "read"]),
        ]
        return [FakeService(chars)]

    monkeypatch.setattr(ble, "get_services_compat", fake_get_services)

    result = asyncio.run(ble.list_notify_characteristics(object()))
    assert result == ["uuid-1", "uuid-3"]


def test_start_notify_best_effort():
    client = FakeBleakClient("AA:BB")

    async def run():
        return await ble.start_notify_best_effort(
            client,
            ["good-1", "bad-1", "good-2"],
            lambda _uuid: lambda _sender, _data: None,
        )

    active = asyncio.run(run())
    assert active == ["good-1", "good-2"]


def test_stop_notify_best_effort():
    client = FakeBleakClient("AA:BB")

    async def run():
        await ble.stop_notify_best_effort(client, ["good-1", "bad-1"])

    asyncio.run(run())
