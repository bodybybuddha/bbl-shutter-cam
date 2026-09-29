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
    monkeypatch.setattr(
        cli,
        "load_profile",
        lambda _path, _name: {"device": {"mac": "AA:BB", "notify_uuid": "uuid"}},
    )
    monkeypatch.setattr(cli.discover, "run_profile", fake_run_profile)

    args = argparse.Namespace(
        config=tmp_path / "config.toml",
        profile="office",
        dry_run=True,
        verbose=False,
        reconnect_delay=0.1,
        web_port=None,
        enable_stream=False,
        stream_resolution=None,
        stream_fps=None,
    )
    rc = cli._cmd_run(args)

    assert rc == 0


def test_cmd_run_enable_stream_requires_web_port(monkeypatch, tmp_path):
    """--enable-stream without --web-port should error out, not silently ignore it."""
    monkeypatch.setattr(cli, "ensure_config_exists", lambda _path: None)

    args = argparse.Namespace(
        config=tmp_path / "config.toml",
        profile="office",
        dry_run=True,
        verbose=False,
        reconnect_delay=0.1,
        web_port=None,
        enable_stream=True,
        stream_resolution=None,
        stream_fps=None,
    )
    rc = cli._cmd_run(args)

    assert rc == 1


def test_cmd_run_with_web_port_runs_both(monkeypatch, tmp_path):
    """When --web-port is set, both the BLE loop and the web server should run."""
    calls = []

    async def fake_run_profile(*_args, **_kwargs):
        calls.append("ble")

    async def fake_run_server(_app, _host, _port):
        calls.append("web")

    monkeypatch.setattr(cli, "ensure_config_exists", lambda _path: None)
    monkeypatch.setattr(
        cli,
        "load_profile",
        lambda _path, _name: {"device": {"mac": "AA:BB", "notify_uuid": "uuid"}},
    )
    monkeypatch.setattr(cli.discover, "run_profile", fake_run_profile)

    # cli._cmd_run does a function-local `from . import streaming`, which
    # resolves via the bbl_shutter_cam package's `streaming` attribute once
    # the real module has been imported anywhere (e.g. by test_streaming.py
    # at collection time) - patching sys.modules alone doesn't intercept
    # that. Patch the real module's functions in place instead.
    streaming = pytest.importorskip("bbl_shutter_cam.streaming")
    monkeypatch.setattr(
        streaming, "create_app", lambda _cam_cfg, _stream_cfg, enable_stream=False: object()
    )
    monkeypatch.setattr(streaming, "run_server", fake_run_server)

    args = argparse.Namespace(
        config=tmp_path / "config.toml",
        profile="office",
        dry_run=True,
        verbose=False,
        reconnect_delay=0.1,
        web_port=8080,
        enable_stream=False,
        stream_resolution=None,
        stream_fps=None,
    )
    rc = cli._cmd_run(args)

    assert rc == 0
    assert set(calls) == {"ble", "web"}


def test_cmd_run_stream_overrides_apply(monkeypatch, tmp_path):
    """--stream-resolution/--stream-fps should override the profile's stream config."""

    async def fake_run_profile(*_args, **_kwargs):
        return None

    async def fake_run_server(_app, _host, _port):
        return None

    seen_stream_cfg = {}

    def fake_create_app(_cam_cfg, stream_cfg, enable_stream=False):
        seen_stream_cfg["width"] = stream_cfg.width
        seen_stream_cfg["height"] = stream_cfg.height
        seen_stream_cfg["fps"] = stream_cfg.fps
        seen_stream_cfg["enable_stream"] = enable_stream
        return object()

    monkeypatch.setattr(cli, "ensure_config_exists", lambda _path: None)
    monkeypatch.setattr(
        cli,
        "load_profile",
        lambda _path, _name: {"device": {"mac": "AA:BB", "notify_uuid": "uuid"}},
    )
    monkeypatch.setattr(cli.discover, "run_profile", fake_run_profile)

    streaming = pytest.importorskip("bbl_shutter_cam.streaming")
    monkeypatch.setattr(streaming, "create_app", fake_create_app)
    monkeypatch.setattr(streaming, "run_server", fake_run_server)

    args = argparse.Namespace(
        config=tmp_path / "config.toml",
        profile="office",
        dry_run=True,
        verbose=False,
        reconnect_delay=0.1,
        web_port=8080,
        enable_stream=True,
        stream_resolution="1920x1080",
        stream_fps=30,
    )
    rc = cli._cmd_run(args)

    assert rc == 0
    assert seen_stream_cfg == {
        "width": 1920,
        "height": 1080,
        "fps": 30,
        "enable_stream": True,
    }
