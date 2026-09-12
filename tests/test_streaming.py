"""Unit tests for streaming.py module.

Tests the optional web server's routes without touching the real camera.
The /stream route's full 200-success path (an async generator gated on
client-disconnect/timeout) is deliberately not driven through TestClient,
since that risks hanging or slow tests; StreamSession's underlying logic
is unit-tested directly instead, and the route is only checked for its
fast-return gating (disabled -> 404, already-in-use -> 409).
"""

import subprocess

import pytest

fastapi_testclient = pytest.importorskip(
    "fastapi.testclient", reason="fastapi[web] extra not installed"
)
TestClient = fastapi_testclient.TestClient

from bbl_shutter_cam import streaming  # noqa: E402
from bbl_shutter_cam.camera import CameraConfig, StreamConfig  # noqa: E402


@pytest.fixture
def cam_cfg(tmp_path):
    return CameraConfig(output_dir=str(tmp_path))


@pytest.fixture
def stream_cfg():
    return StreamConfig()


def _make_client(cam_cfg, stream_cfg, enable_stream=False):
    app = streaming.create_app(cam_cfg, stream_cfg, enable_stream=enable_stream)
    return TestClient(app), app


@pytest.fixture
def client(cam_cfg, stream_cfg):
    c, _app = _make_client(cam_cfg, stream_cfg)
    return c


def _write_fake_jpeg(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    path = str(path)
    with open(path, "wb") as f:
        f.write(b"\xff\xd8\xff\xe0fakejpegdata")
    return path


class TestIndex:
    def test_index_returns_html(self, client):
        resp = client.get("/")
        assert resp.status_code == 200
        assert "text/html" in resp.headers["content-type"]
        assert "bbl-shutter-cam" in resp.text
        assert "/snapshot" in resp.text
        assert "/capture" in resp.text

    def test_index_omits_stream_button_when_disabled(self, cam_cfg, stream_cfg):
        client, _app = _make_client(cam_cfg, stream_cfg, enable_stream=False)
        resp = client.get("/")
        assert "Start live stream" not in resp.text

    def test_index_includes_stream_button_when_enabled(self, cam_cfg, stream_cfg):
        client, _app = _make_client(cam_cfg, stream_cfg, enable_stream=True)
        resp = client.get("/")
        assert "Start live stream" in resp.text


class TestSnapshot:
    def test_snapshot_returns_jpeg(self, monkeypatch, client, tmp_path):
        outfile = _write_fake_jpeg(tmp_path / "web" / "snapshot.jpg")

        async def fake_capture_preview(_cam_cfg):
            return outfile

        monkeypatch.setattr(streaming, "capture_preview", fake_capture_preview)

        resp = client.get("/snapshot")

        assert resp.status_code == 200
        assert resp.headers["content-type"] == "image/jpeg"
        assert resp.content.startswith(b"\xff\xd8\xff")

    def test_snapshot_failure_returns_503(self, monkeypatch, client):
        async def fake_capture_preview(_cam_cfg):
            raise RuntimeError("camera busy")

        monkeypatch.setattr(streaming, "capture_preview", fake_capture_preview)

        resp = client.get("/snapshot")

        assert resp.status_code == 503


class TestCapture:
    def test_capture_returns_jpeg(self, monkeypatch, client, tmp_path):
        outfile = _write_fake_jpeg(tmp_path / "20260101_000000.jpg")

        async def fake_capture_still(_cam_cfg, capture_mode="frame"):
            return outfile

        monkeypatch.setattr(streaming, "capture_still", fake_capture_still)

        resp = client.post("/capture")

        assert resp.status_code == 200
        assert resp.headers["content-type"] == "image/jpeg"
        assert resp.content.startswith(b"\xff\xd8\xff")

    def test_capture_passes_configured_capture_mode(self, monkeypatch, cam_cfg, tmp_path):
        outfile = _write_fake_jpeg(tmp_path / "20260101_000000.jpg")
        seen = {}

        async def fake_capture_still(_cam_cfg, capture_mode="frame"):
            seen["mode"] = capture_mode
            return outfile

        monkeypatch.setattr(streaming, "capture_still", fake_capture_still)

        client, _app = _make_client(cam_cfg, StreamConfig(capture_mode="pause"))
        resp = client.post("/capture")

        assert resp.status_code == 200
        assert seen["mode"] == "pause"

    def test_capture_failure_returns_503(self, monkeypatch, client):
        async def fake_capture_still(_cam_cfg, capture_mode="frame"):
            raise RuntimeError("rpicam-still failed")

        monkeypatch.setattr(streaming, "capture_still", fake_capture_still)

        resp = client.post("/capture")

        assert resp.status_code == 503

    def test_capture_is_post_only(self, client):
        resp = client.get("/capture")
        assert resp.status_code == 405


class TestStreamRouteGating:
    """Only the fast-return paths - the 200 success path is a long-lived
    generator, unit-tested via StreamSession instead (see below)."""

    def test_stream_404_when_not_enabled(self, client):
        resp = client.get("/stream")
        assert resp.status_code == 404

    def test_stream_409_when_already_in_use(self, cam_cfg, stream_cfg):
        client, app = _make_client(cam_cfg, stream_cfg, enable_stream=True)
        session = app.state.stream_session
        assert session.claim_viewer() is True  # simulate an existing viewer

        resp = client.get("/stream")

        assert resp.status_code == 409


class FakeProcess:
    """Stand-in for subprocess.Popen, feeding canned stdout chunks."""

    def __init__(self, chunks):
        self._chunks = list(chunks)
        self._idx = 0
        self.stdout = self
        self.terminated = False
        self.killed = False

    def read(self, _n=4096):
        if self._idx >= len(self._chunks):
            return b""
        chunk = self._chunks[self._idx]
        self._idx += 1
        return chunk

    def terminate(self):
        self.terminated = True

    def wait(self, timeout=None):
        if not self.terminated:
            raise subprocess.TimeoutExpired(cmd="rpicam-vid", timeout=timeout)

    def kill(self):
        self.killed = True


FRAME_1 = b"\xff\xd8FRAME-ONE\xff\xd9"
FRAME_2 = b"\xff\xd8FRAME-TWO\xff\xd9"


class TestStreamSession:
    def test_drain_frames_extracts_complete_frames(self, cam_cfg, stream_cfg):
        session = streaming.StreamSession(cam_cfg, stream_cfg)

        remainder = session._drain_frames(FRAME_1 + FRAME_2)

        assert remainder == b""
        assert session.next_frame(timeout=0.1) == FRAME_1
        assert session.next_frame(timeout=0.1) == FRAME_2

    def test_drain_frames_holds_partial_frame(self, cam_cfg, stream_cfg):
        session = streaming.StreamSession(cam_cfg, stream_cfg)
        partial = FRAME_1[:5]

        remainder = session._drain_frames(partial)

        assert remainder == partial
        assert session.next_frame(timeout=0.1) is None

    def test_read_loop_publishes_frames_and_updates_latest_frame(
        self, monkeypatch, cam_cfg, stream_cfg
    ):
        from bbl_shutter_cam.camera import LATEST_FRAME

        proc = FakeProcess([FRAME_1, FRAME_2, b""])
        session = streaming.StreamSession(cam_cfg, stream_cfg)
        session._proc = proc

        session._read_loop()

        assert session.next_frame(timeout=0.1) == FRAME_1
        assert session.next_frame(timeout=0.1) == FRAME_2
        assert LATEST_FRAME.get_if_fresh() == FRAME_2
        LATEST_FRAME.clear()

    def test_start_spawns_popen_via_camera_lock(self, monkeypatch, cam_cfg, stream_cfg):
        spawned = {}

        def fake_popen(cmd, **kwargs):
            spawned["cmd"] = cmd
            return FakeProcess([b""])

        monkeypatch.setattr(streaming.subprocess, "Popen", fake_popen)

        session = streaming.StreamSession(cam_cfg, stream_cfg)
        session.start()
        session._reader_thread.join(timeout=2)

        assert spawned["cmd"][0] == "rpicam-vid"
        assert session._proc is not None

        session.stop()
        assert session._proc is None

    def test_stop_terminates_process_and_clears_latest_frame(
        self, monkeypatch, cam_cfg, stream_cfg
    ):
        from bbl_shutter_cam.camera import LATEST_FRAME

        monkeypatch.setattr(streaming.subprocess, "Popen", lambda cmd, **kw: FakeProcess([b""]))
        session = streaming.StreamSession(cam_cfg, stream_cfg)
        session.start()
        session._reader_thread.join(timeout=2)
        LATEST_FRAME.update(FRAME_1)

        proc = session._proc
        session.stop()

        assert proc.terminated is True
        assert LATEST_FRAME.get_if_fresh() is None

    def test_pause_and_capture_stops_captures_and_restarts(self, monkeypatch, cam_cfg, tmp_path):
        popen_calls = []

        def fake_popen(cmd, **kwargs):
            popen_calls.append(cmd)
            return FakeProcess([b""])

        run_calls = []

        def fake_run(cmd, **kwargs):
            run_calls.append(cmd)

        monkeypatch.setattr(streaming.subprocess, "Popen", fake_popen)
        monkeypatch.setattr(streaming.subprocess, "run", fake_run)
        monkeypatch.setattr(streaming, "make_outfile", lambda _cfg: str(tmp_path / "still.jpg"))

        stream_cfg = StreamConfig(capture_mode="pause")
        session = streaming.StreamSession(cam_cfg, stream_cfg)
        session.start()
        session._reader_thread.join(timeout=2)
        first_proc = session._proc

        outfile = session._pause_and_capture()

        assert outfile == str(tmp_path / "still.jpg")
        assert first_proc.terminated is True  # old stream process was stopped
        assert len(popen_calls) == 2  # initial start + restart after capture
        assert len(run_calls) == 1  # exactly one rpicam-still capture
        assert run_calls[0][0] == "rpicam-still"
        assert session._proc is not None  # stream was restarted

        session.stop()

    def test_pause_mode_registers_with_stream_controller(self, monkeypatch, cam_cfg):
        from bbl_shutter_cam.camera import STREAM_CONTROLLER

        monkeypatch.setattr(streaming.subprocess, "Popen", lambda cmd, **kw: FakeProcess([b""]))

        stream_cfg = StreamConfig(capture_mode="pause")
        session = streaming.StreamSession(cam_cfg, stream_cfg)
        session.start()
        session._reader_thread.join(timeout=2)

        registered = STREAM_CONTROLLER._pause_and_capture  # pylint: disable=protected-access
        assert registered == session._pause_and_capture  # bound methods: == not is

        session.stop()
        assert STREAM_CONTROLLER._pause_and_capture is None  # pylint: disable=protected-access

    def test_frame_mode_does_not_register_with_stream_controller(
        self, monkeypatch, cam_cfg, stream_cfg
    ):
        from bbl_shutter_cam.camera import STREAM_CONTROLLER

        monkeypatch.setattr(streaming.subprocess, "Popen", lambda cmd, **kw: FakeProcess([b""]))

        session = streaming.StreamSession(cam_cfg, stream_cfg)  # default capture_mode="frame"
        session.start()
        session._reader_thread.join(timeout=2)

        assert STREAM_CONTROLLER._pause_and_capture is None  # pylint: disable=protected-access

        session.stop()

    def test_claim_and_release_viewer(self, cam_cfg, stream_cfg):
        session = streaming.StreamSession(cam_cfg, stream_cfg)

        assert session.claim_viewer() is True
        assert session.claim_viewer() is False  # already claimed
        assert session.has_viewer() is True

        session.release_viewer()

        assert session.has_viewer() is False
        assert session.claim_viewer() is True
