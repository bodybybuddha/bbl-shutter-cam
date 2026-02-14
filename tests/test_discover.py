"""Unit tests for discover.py module."""
import asyncio
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import pytest
from tomlkit import document, dumps

from bbl_shutter_cam import discover
from bbl_shutter_cam.config import load_config


@dataclass
class FakeDevice:
    name: Optional[str]
    address: str


def test_scan_filters_by_name(monkeypatch):
    async def fake_discover(timeout=8.0):
        return [
            FakeDevice(name="BBL_SHUTTER", address="AA:BB"),
            FakeDevice(name="Other", address="CC:DD"),
            FakeDevice(name=None, address="EE:FF"),
        ]

    monkeypatch.setattr(discover.BleakScanner, "discover", fake_discover)

    hits = asyncio.run(discover.scan(name_filter="BBL_SHUTTER", timeout=0.1))
    assert len(hits) == 1
    assert hits[0].address == "AA:BB"

    all_hits = asyncio.run(discover.scan(name_filter=None, timeout=0.1))
    assert len(all_hits) == 3


def test_setup_profile_uses_scan_and_updates_config(monkeypatch, tmp_path):
    async def fake_scan(name_filter=None, timeout=8.0):
        return [FakeDevice(name=name_filter, address="11:22")]

    async def fake_learn(mac, press_timeout=30.0, verbose=False):
        assert mac == "11:22"
        return "notify-uuid"

    captured = {}

    def fake_update(config_path, profile, mac, notify_uuid):
        captured["path"] = config_path
        captured["profile"] = profile
        captured["mac"] = mac
        captured["notify_uuid"] = notify_uuid

    monkeypatch.setattr(discover, "scan", fake_scan)
    monkeypatch.setattr(discover, "learn_notify_uuid", fake_learn)
    monkeypatch.setattr(discover, "update_profile_device_fields", fake_update)

    result = asyncio.run(
        discover.setup_profile(
            config_path=tmp_path / "config.toml",
            profile="office",
            device_name="BBL_SHUTTER",
        )
    )

    assert result == ("11:22", "notify-uuid")
    assert captured["profile"] == "office"
    assert captured["mac"] == "11:22"
    assert captured["notify_uuid"] == "notify-uuid"


def test_run_profile_requires_mac_and_notify_uuid():
    profile = {"device": {}}

    with pytest.raises(SystemExit, match="device.mac"):
        asyncio.run(discover.run_profile(profile))

    profile = {"device": {"mac": "AA:BB"}}
    with pytest.raises(SystemExit, match="device.notify_uuid"):
        asyncio.run(discover.run_profile(profile))


def test_update_config_with_signals(tmp_path):
    config_path = tmp_path / "config.toml"
    cfg = document()
    cfg["profiles"] = document()
    cfg["profiles"]["office"] = {"device": {}}
    config_path.write_text(dumps(cfg))

    seen_data = {
        "uuid-1": [bytes.fromhex("4000"), bytes.fromhex("0000"), bytes.fromhex("4000")],
        "uuid-2": [bytes.fromhex("8000")],
    }

    discover._update_config_with_signals(config_path, "office", seen_data)

    updated = load_config(config_path)
    events = updated["profiles"]["office"]["device"]["events"]

    assert len(events) == 3
    # Ensure release signal is marked non-capturing
    release = [e for e in events if e["hex"] == "0000"][0]
    assert release["capture"] is False


def test_debug_signals_updates_config(monkeypatch, tmp_path):
    class FakeClient:
        def __init__(self):
            self.is_connected = True

        async def start_notify(self, _uuid, callback):
            callback(0, bytearray.fromhex("4000"))

        async def disconnect(self):
            self.is_connected = False

    async def fake_connect(_mac):
        return FakeClient()

    async def fake_list_notify(_client):
        return ["uuid-1"]

    async def fake_sleep(_duration):
        return None

    called = {}

    def fake_update(config_path, profile_name, seen_data):
        called["path"] = config_path
        called["profile"] = profile_name
        called["seen"] = seen_data

    monkeypatch.setattr(discover.ble, "connect_with_retry", fake_connect)
    monkeypatch.setattr(discover.ble, "list_notify_characteristics", fake_list_notify)
    monkeypatch.setattr(discover.asyncio, "sleep", fake_sleep)
    monkeypatch.setattr(discover, "_update_config_with_signals", fake_update)

    asyncio.run(
        discover.debug_signals(
            config_path=tmp_path / "config.toml",
            profile_name="office",
            mac="AA:BB",
            duration=0.1,
            update_config=True,
        )
    )

    assert called["profile"] == "office"
    assert "uuid-1" in called["seen"]


def test_run_profile_captures_on_trigger(monkeypatch):
    class FakeClient:
        def __init__(self):
            self.is_connected = True

        async def start_notify(self, _uuid, callback):
            callback(0, bytearray.fromhex("4000"))
            self.is_connected = False

        async def disconnect(self):
            self.is_connected = False

    async def fake_connect(_mac, reconnect_delay=2.0):
        if not hasattr(fake_connect, "called"):
            fake_connect.called = True
            return FakeClient()
        raise KeyboardInterrupt()

    async def fake_sleep(_duration):
        return None

    def fake_make_outfile(_cfg):
        return "/tmp/out.jpg"

    def fake_build_cmd(_cfg, outfile):
        return ["rpicam-still", "-o", outfile]

    def fake_run(_cmd, check=True):
        return None

    monkeypatch.setattr(discover.ble, "connect_with_retry", fake_connect)
    monkeypatch.setattr(discover.asyncio, "sleep", fake_sleep)
    monkeypatch.setattr(discover, "make_outfile", fake_make_outfile)
    monkeypatch.setattr(discover, "build_rpicam_still_cmd", fake_build_cmd)
    monkeypatch.setattr(discover.subprocess, "run", fake_run)

    profile = {
        "_profile_name": "office",
        "device": {
            "mac": "AA:BB",
            "notify_uuid": "uuid-1",
            "events": [{"hex": "4000", "capture": True, "name": "press"}],
        },
        "camera": {
            "output_dir": "/tmp",
            "rpicam": {"width": 1920, "height": 1080},
        },
    }

    asyncio.run(discover.run_profile(profile, dry_run=False))
