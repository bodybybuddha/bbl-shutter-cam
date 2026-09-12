"""Optional HTTP server for on-demand snapshots, manual capture, and live preview.

Runs alongside the BLE listener in the same asyncio event loop when the
user passes --web-port to `run`. Disabled by default; requires the
optional "web" extra:

    pip install bbl-shutter-cam[web]

The Bluetooth shutter remains the primary, zero-latency capture trigger.
This server is a secondary path for remote preview and manual/Home
Assistant-driven capture, per docs/advanced/web-streaming.md.

The live MJPEG stream (/stream) is itself opt-in via --enable-stream, kept
separate from --web-port, so a user who only wants /snapshot and /capture
never exposes streaming capability at all.
"""

from __future__ import annotations

import asyncio
import queue
import subprocess
import threading
import time
from pathlib import Path
from typing import Optional

from .camera import (
    CAMERA_LOCK,
    LATEST_FRAME,
    STREAM_CONTROLLER,
    CameraConfig,
    StreamConfig,
    build_rpicam_still_cmd,
    build_rpicam_vid_mjpeg_cmd,
    capture_preview,
    capture_still,
    make_outfile,
)
from .util import LOG

try:
    import uvicorn
    from fastapi import FastAPI, HTTPException, Request
    from fastapi.responses import FileResponse, HTMLResponse, StreamingResponse
except ImportError as exc:  # pragma: no cover - exercised via CLI error path
    raise ImportError(
        "Web streaming requires extra dependencies that aren't installed. "
        "Install with: pip install bbl-shutter-cam[web]"
    ) from exc


MJPEG_BOUNDARY = "frame"

INDEX_HTML = """<!doctype html>
<html>
<head>
  <title>bbl-shutter-cam</title>
  <meta name="viewport" content="width=device-width, initial-scale=1" />
</head>
<body style="font-family: sans-serif; max-width: 640px; margin: 2rem auto; padding: 0 1rem;">
  <h1>bbl-shutter-cam</h1>
  <img src="{preview_src}" id="preview" alt="camera preview"
       style="max-width: 100%; border: 1px solid #ccc; display: block;" />
  <p>
    <button onclick="refresh()">Refresh preview</button>
    <button onclick="capture()">Capture photo</button>
    {stream_button}
  </p>
  <p id="status"></p>
  <script>
    function refresh() {{
      document.getElementById('preview').src = '/snapshot?' + Date.now();
    }}
    function capture() {{
      const status = document.getElementById('status');
      status.textContent = 'Capturing...';
      fetch('/capture', {{ method: 'POST' }})
        .then(r => {{ if (!r.ok) throw new Error(r.statusText); status.textContent = 'Captured.'; refresh(); }})
        .catch(e => {{ status.textContent = 'Capture failed: ' + e; }});
    }}
    function startStream() {{
      document.getElementById('preview').src = '/stream';
    }}
  </script>
</body>
</html>
"""


class StreamSession:
    """Owns a single rpicam-vid process, feeding MJPEG frames to at most one
    connected /stream client at a time (per docs/advanced/web-streaming.md's
    single-concurrent-stream design for constrained hardware).

    Uses plain threads and subprocess.Popen (not asyncio subprocess) so that
    capture_mode="pause" can stop and restart the process synchronously from
    the BLE notify callback or a capture worker thread, without needing to
    schedule work back onto the event loop.
    """

    def __init__(self, cam_cfg: CameraConfig, stream_cfg: StreamConfig) -> None:
        self.cam_cfg = cam_cfg
        self.stream_cfg = stream_cfg
        self._lock = threading.Lock()
        self._proc: Optional[subprocess.Popen] = None
        self._reader_thread: Optional[threading.Thread] = None
        self._frame_queue: "queue.Queue[Optional[bytes]]" = queue.Queue(maxsize=2)
        self._has_viewer = False

    def has_viewer(self) -> bool:
        """Whether a client is currently claimed as the active viewer."""
        return self._has_viewer

    def claim_viewer(self) -> bool:
        """Try to become the single active viewer. Returns False if one is
        already attached."""
        with self._lock:
            if self._has_viewer:
                return False
            self._has_viewer = True
            return True

    def release_viewer(self) -> None:
        """Give up the single-viewer slot and stop the stream process."""
        with self._lock:
            self._has_viewer = False
        self.stop()

    def next_frame(self, timeout: float = 1.0) -> Optional[bytes]:
        """Block briefly for the next frame. Returns None on stream end/timeout."""
        try:
            return self._frame_queue.get(timeout=timeout)
        except queue.Empty:
            return None

    def start(self) -> None:
        """Spawn rpicam-vid and start reading frames from it, if not already running."""
        with self._lock:
            self._start_locked()
            if self.stream_cfg.capture_mode == "pause":
                STREAM_CONTROLLER.register(self._pause_and_capture)

    def stop(self) -> None:
        """Terminate rpicam-vid (if running) and clear stream-related shared state."""
        with self._lock:
            self._stop_locked()
            STREAM_CONTROLLER.unregister()
        LATEST_FRAME.clear()
        # Unblock anyone waiting in next_frame().
        try:
            self._frame_queue.put_nowait(None)
        except queue.Full:
            pass

    def _start_locked(self) -> None:
        if self._proc is not None:
            return
        cmd = build_rpicam_vid_mjpeg_cmd(self.stream_cfg, self.cam_cfg)
        LOG.debug(f"Stream cmd: {' '.join(cmd)}")
        with CAMERA_LOCK:
            self._proc = subprocess.Popen(  # pylint: disable=consider-using-with
                cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL
            )
        self._reader_thread = threading.Thread(target=self._read_loop, daemon=True)
        self._reader_thread.start()

    def _stop_locked(self) -> None:
        if self._proc is None:
            return
        self._proc.terminate()
        try:
            self._proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            self._proc.kill()
        self._proc = None

    def _read_loop(self) -> None:
        proc = self._proc
        if proc is None or proc.stdout is None:
            return
        buf = b""
        while True:
            chunk = proc.stdout.read(4096)
            if not chunk:
                break
            buf += chunk
            buf = self._drain_frames(buf)
        try:
            self._frame_queue.put_nowait(None)
        except queue.Full:
            pass

    def _drain_frames(self, buf: bytes) -> bytes:
        """Extract complete JPEG frames (SOI 0xFFD8 ... EOI 0xFFD9) from buf,
        publishing each one, and return the unconsumed remainder."""
        while True:
            start = buf.find(b"\xff\xd8")
            if start == -1:
                return b""
            end = buf.find(b"\xff\xd9", start)
            if end == -1:
                return buf[start:]
            frame = buf[start : end + 2]
            buf = buf[end + 2 :]
            self._publish_frame(frame)

    def _publish_frame(self, frame: bytes) -> None:
        LATEST_FRAME.update(frame)
        try:
            self._frame_queue.put_nowait(frame)
        except queue.Full:
            try:
                self._frame_queue.get_nowait()  # drop the oldest, keep it live
            except queue.Empty:
                pass
            try:
                self._frame_queue.put_nowait(frame)
            except queue.Full:
                pass

    def _pause_and_capture(self) -> str:
        """Registered with STREAM_CONTROLLER when capture_mode="pause":
        called synchronously (from the BLE notify callback or a capture
        worker thread) to pause the stream, take a full-quality still, and
        resume streaming. Returns the still's path.

        Runs under self._lock so a still request can't race a client
        connecting/disconnecting the stream at the same moment.
        """
        with self._lock:
            self._stop_locked()
            outfile = make_outfile(self.cam_cfg)
            cmd = build_rpicam_still_cmd(self.cam_cfg, outfile)
            LOG.debug(f"Pause-mode capture cmd: {' '.join(cmd)}")
            with CAMERA_LOCK:
                subprocess.run(cmd, check=True, capture_output=True)
            self._start_locked()
        return outfile


def create_app(
    cam_cfg: CameraConfig,
    stream_cfg: StreamConfig,
    enable_stream: bool = False,
) -> FastAPI:
    """Build the FastAPI app for a given camera/stream configuration.

    Args:
        cam_cfg: Camera configuration for still captures and preview.
        stream_cfg: Stream configuration for the optional /stream route.
        enable_stream: If False (default), /stream returns 404 even though
            the rest of the web server is active — streaming is opt-in on
            top of --web-port, not automatically available.

    Returns:
        FastAPI: Configured app with /, /snapshot, /capture, and (if enabled)
            /stream routes.
    """
    app = FastAPI(title="bbl-shutter-cam")
    session = StreamSession(cam_cfg, stream_cfg)
    app.state.stream_session = session  # exposed mainly for tests

    @app.get("/", response_class=HTMLResponse)
    async def index() -> str:
        stream_button = (
            '<button onclick="startStream()">Start live stream</button>' if enable_stream else ""
        )
        return INDEX_HTML.format(preview_src="/snapshot", stream_button=stream_button)

    @app.get("/snapshot")
    async def snapshot() -> FileResponse:
        try:
            outfile = await capture_preview(cam_cfg)
        except Exception as exc:
            LOG.error(f"Snapshot failed: {exc}")
            raise HTTPException(status_code=503, detail="Snapshot capture failed") from exc
        return FileResponse(outfile, media_type="image/jpeg")

    @app.post("/capture")
    async def capture() -> FileResponse:
        try:
            outfile = await capture_still(cam_cfg, capture_mode=stream_cfg.capture_mode)
        except Exception as exc:
            LOG.error(f"Manual capture failed: {exc}")
            raise HTTPException(status_code=503, detail="Capture failed") from exc
        LOG.info(f"Manual web capture: {outfile}")
        return FileResponse(outfile, media_type="image/jpeg", filename=Path(outfile).name)

    @app.get("/stream")
    async def stream(request: Request) -> StreamingResponse:
        if not enable_stream:
            raise HTTPException(
                status_code=404, detail="Streaming is not enabled (--enable-stream)"
            )
        if not session.claim_viewer():
            raise HTTPException(status_code=409, detail="Stream already in use")

        async def frame_generator():
            # A None from next_frame() means either "no frame within the
            # poll timeout" (normal) or "the reader thread ended" - which
            # also happens for a brief capture_mode="pause" restart, not
            # just a genuine crash. Only give up once nothing has arrived
            # for STALL_LIMIT seconds straight, which a pause comfortably
            # fits under.
            STALL_LIMIT = 10.0
            try:
                session.start()
                start_time = time.monotonic()
                last_frame_time = start_time
                while True:
                    if await request.is_disconnected():
                        break
                    now = time.monotonic()
                    if now - start_time > stream_cfg.timeout_seconds:
                        LOG.info("Stream auto-timeout reached.")
                        break
                    frame = await asyncio.to_thread(session.next_frame)
                    if frame is None:
                        if now - last_frame_time > STALL_LIMIT:
                            LOG.warning("No stream frames for %.0fs; ending stream.", STALL_LIMIT)
                            break
                        continue
                    last_frame_time = now
                    yield (
                        f"--{MJPEG_BOUNDARY}\r\n"
                        "Content-Type: image/jpeg\r\n"
                        f"Content-Length: {len(frame)}\r\n\r\n"
                    ).encode() + frame + b"\r\n"
            finally:
                session.release_viewer()

        return StreamingResponse(
            frame_generator(),
            media_type=f"multipart/x-mixed-replace; boundary={MJPEG_BOUNDARY}",
        )

    return app


async def run_server(app: FastAPI, host: str, port: int) -> None:
    """Run the FastAPI app via uvicorn inside the current asyncio event loop.

    Args:
        app: FastAPI app, typically from create_app().
        host: Bind address (e.g. "0.0.0.0" for LAN access).
        port: Port to listen on.
    """
    config = uvicorn.Config(app, host=host, port=port, log_level="warning")
    server = uvicorn.Server(config)
    LOG.info(f"Web server listening on http://{host}:{port}")
    await server.serve()
