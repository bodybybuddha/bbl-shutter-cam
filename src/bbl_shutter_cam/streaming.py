"""Optional HTTP server for on-demand snapshots and manual capture triggers.

Runs alongside the BLE listener in the same asyncio event loop when the
user passes --web-port to `run`. Disabled by default; requires the
optional "web" extra:

    pip install bbl-shutter-cam[web]

The Bluetooth shutter remains the primary, zero-latency capture trigger.
This server is a secondary path for remote preview and manual/Home
Assistant-driven capture, per docs/advanced/web-streaming.md.
"""

from __future__ import annotations

from pathlib import Path

from .camera import CameraConfig, capture_preview, capture_still
from .util import LOG

try:
    import uvicorn
    from fastapi import FastAPI, HTTPException
    from fastapi.responses import FileResponse, HTMLResponse
except ImportError as exc:  # pragma: no cover - exercised via CLI error path
    raise ImportError(
        "Web streaming requires extra dependencies that aren't installed. "
        "Install with: pip install bbl-shutter-cam[web]"
    ) from exc


INDEX_HTML = """<!doctype html>
<html>
<head>
  <title>bbl-shutter-cam</title>
  <meta name="viewport" content="width=device-width, initial-scale=1" />
</head>
<body style="font-family: sans-serif; max-width: 640px; margin: 2rem auto; padding: 0 1rem;">
  <h1>bbl-shutter-cam</h1>
  <img src="/snapshot" id="preview" alt="camera preview"
       style="max-width: 100%; border: 1px solid #ccc; display: block;" />
  <p>
    <button onclick="refresh()">Refresh preview</button>
    <button onclick="capture()">Capture photo</button>
  </p>
  <p id="status"></p>
  <script>
    function refresh() {
      document.getElementById('preview').src = '/snapshot?' + Date.now();
    }
    function capture() {
      const status = document.getElementById('status');
      status.textContent = 'Capturing...';
      fetch('/capture', { method: 'POST' })
        .then(r => { if (!r.ok) throw new Error(r.statusText); status.textContent = 'Captured.'; refresh(); })
        .catch(e => { status.textContent = 'Capture failed: ' + e; });
    }
  </script>
</body>
</html>
"""


def create_app(cam_cfg: CameraConfig) -> FastAPI:
    """Build the FastAPI app for a given camera configuration.

    Args:
        cam_cfg: Camera configuration to use for both preview snapshots and
            manual captures.

    Returns:
        FastAPI: Configured app with /, /snapshot, and /capture routes.
    """
    app = FastAPI(title="bbl-shutter-cam")

    @app.get("/", response_class=HTMLResponse)
    async def index() -> str:
        return INDEX_HTML

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
            outfile = await capture_still(cam_cfg)
        except Exception as exc:
            LOG.error(f"Manual capture failed: {exc}")
            raise HTTPException(status_code=503, detail="Capture failed") from exc
        LOG.info(f"Manual web capture: {outfile}")
        return FileResponse(outfile, media_type="image/jpeg", filename=Path(outfile).name)

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
