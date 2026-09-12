"""Unit tests for streaming.py module.

Tests the optional web server's routes without touching the real camera.
"""

import pytest

fastapi_testclient = pytest.importorskip(
    "fastapi.testclient", reason="fastapi[web] extra not installed"
)
TestClient = fastapi_testclient.TestClient

from bbl_shutter_cam import streaming  # noqa: E402
from bbl_shutter_cam.camera import CameraConfig  # noqa: E402


@pytest.fixture
def cam_cfg(tmp_path):
    return CameraConfig(output_dir=str(tmp_path))


@pytest.fixture
def client(cam_cfg):
    app = streaming.create_app(cam_cfg)
    return TestClient(app)


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

        async def fake_capture_still(_cam_cfg):
            return outfile

        monkeypatch.setattr(streaming, "capture_still", fake_capture_still)

        resp = client.post("/capture")

        assert resp.status_code == 200
        assert resp.headers["content-type"] == "image/jpeg"
        assert resp.content.startswith(b"\xff\xd8\xff")

    def test_capture_failure_returns_503(self, monkeypatch, client):
        async def fake_capture_still(_cam_cfg):
            raise RuntimeError("rpicam-still failed")

        monkeypatch.setattr(streaming, "capture_still", fake_capture_still)

        resp = client.post("/capture")

        assert resp.status_code == 503

    def test_capture_is_post_only(self, client):
        resp = client.get("/capture")
        assert resp.status_code == 405
