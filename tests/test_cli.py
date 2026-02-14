"""Unit tests for cli.py module."""
import argparse

import pytest

from bbl_shutter_cam import cli


class FakeDevice:
    def __init__(self, name, address):
        self.name = name
        self.address = address

def test_build_parser_requires_command():
    parser = cli._build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args([])


def test_build_parser_parses_tune_command():
    parser = cli._build_parser()
    args = parser.parse_args(["tune", "--profile", "office"])

    assert args.command == "tune"
    assert args.profile == "office"
    assert isinstance(args.config, object)


def test_main_dispatches_to_command(monkeypatch):
    called = {}

    def fake_cmd(_args: argparse.Namespace) -> int:
        called["ran"] = True
        return 0

    monkeypatch.setattr(cli, "_cmd_tune", fake_cmd)

    def fake_configure_logging(**_kwargs):
        called["logging"] = True

    monkeypatch.setattr(cli, "configure_logging", fake_configure_logging)

    with pytest.raises(SystemExit) as exc:
        cli.main(["tune", "--profile", "office"])

    assert exc.value.code == 0
    assert called.get("ran") is True
    assert called.get("logging") is True


def test_main_exits_when_missing_command():
    with pytest.raises(SystemExit) as exc:
        cli.main([])

    assert exc.value.code == 2


def test_cmd_scan_no_devices(monkeypatch):
    async def fake_scan(**_kwargs):
        return []

    monkeypatch.setattr(cli.discover, "scan", fake_scan)

    args = argparse.Namespace(name=None, timeout=0.1)
    rc = cli._cmd_scan(args)

    assert rc == 1


def test_cmd_scan_lists_devices(monkeypatch, capsys):
    async def fake_scan(**_kwargs):
        return [FakeDevice("BBL_SHUTTER", "AA:BB")]

    monkeypatch.setattr(cli.discover, "scan", fake_scan)

    args = argparse.Namespace(name=None, timeout=0.1)
    rc = cli._cmd_scan(args)

    assert rc == 0
    out = capsys.readouterr().out
    assert "AA:BB" in out


def test_cmd_setup_success(monkeypatch, tmp_path, capsys):
    async def fake_setup(**_kwargs):
        return ("AA:BB", "uuid-1")

    monkeypatch.setattr(cli.discover, "setup_profile", fake_setup)
    monkeypatch.setattr(cli, "ensure_config_exists", lambda _path: None)

    args = argparse.Namespace(
        config=tmp_path / "config.toml",
        profile="office",
        name="BBL_SHUTTER",
        mac=None,
        timeout=0.1,
        press_timeout=0.1,
        verbose=False,
    )
    rc = cli._cmd_setup(args)

    assert rc == 0
    out = capsys.readouterr().out
    assert "AA:BB" in out


def test_cmd_debug_requires_mac(monkeypatch, tmp_path):
    monkeypatch.setattr(cli, "ensure_config_exists", lambda _path: None)
    monkeypatch.setattr(cli, "load_profile", lambda _path, _name: {"device": {}})

    args = argparse.Namespace(
        config=tmp_path / "config.toml",
        profile="office",
        mac=None,
        duration=0.1,
        update_config=False,
    )
    rc = cli._cmd_debug(args)

    assert rc == 1


def test_cmd_run_invokes_discover(monkeypatch, tmp_path):
    async def fake_run_profile(*_args, **_kwargs):
        return None

    monkeypatch.setattr(cli, "ensure_config_exists", lambda _path: None)
    monkeypatch.setattr(cli, "load_profile", lambda _path, _name: {"device": {"mac": "AA:BB", "notify_uuid": "uuid"}})
    monkeypatch.setattr(cli.discover, "run_profile", fake_run_profile)

    args = argparse.Namespace(
        config=tmp_path / "config.toml",
        profile="office",
        dry_run=True,
        verbose=False,
        reconnect_delay=0.1,
    )
    rc = cli._cmd_run(args)

    assert rc == 0
