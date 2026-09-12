# Web Streaming & Home Assistant Integration

## Overview

Web streaming and Home Assistant integration is a feature for bbl-shutter-cam that enables remote monitoring of your Raspberry Pi camera via a web interface and integration with Home Assistant. This allows you to view live camera feeds and remote snapshots while maintaining the **Bluetooth shutter as the primary trigger** for reliable time-lapse capture.

**Status**: Phase 1 implemented (`/snapshot`, `/capture`, minimal web UI, `--web-port` flag). Live MJPEG `/stream` (Phase 2) and full Home Assistant docs/MQTT (Phase 3) are still planned.
**Target Device**: Raspberry Pi Zero 2W (and larger models)

---

## Why Web Streaming?

### Use Cases

1. **Remote Monitoring**: Check your 3D print progress from another room or device
2. **Home Assistant Integration**: Include your camera feed in your smart home dashboard
3. **Live Preview**: Verify camera positioning and lighting before starting a print
4. **Troubleshooting**: Visually diagnose issues with camera angle, focus, or lighting

### Design Philosophy

- **Optional & Lightweight**: Disabled by default; enabled only when you need it
- **On-Demand**: Stream starts when you access it, stops automatically when idle
- **Bluetooth-First**: The physical Bluetooth shutter remains the preferred trigger for consistent time-lapses
- **Zero Latency Between Shutter & Capture**: Photo is captured instantly on button press, with no web server intervention

---

## Architecture

### Single Process Design

The web server and Bluetooth listener run in the **same systemd service**:

```
bbl-shutter-cam run --profile my-printer --web-port 8080
    ↓
    └─ BLE listener (always active)
    └─ FastAPI/uvicorn web server (optional, if --web-port specified)
```

Both run in the same asyncio event loop (`asyncio.gather`) — FastAPI/uvicorn was chosen over Flask specifically because the BLE listener is already fully async (`bleak`), so the web server can share that loop natively instead of needing a separate thread to bridge a synchronous WSGI framework in.

This keeps the deployment simple and reduces resource overhead compared to separate services.

### Capture Paths

**Path 1: Bluetooth Shutter (Primary)**
```
Physical shutter press → BLE signal → rpicam-still capture → photo saved
```
- Reliable, no network dependency
- Best for time-lapse sequences
- Zero software latency

**Path 2: Web UI or Home Assistant (Secondary)** ✅ Implemented
```
Web button click → FastAPI endpoint → rpicam-still capture → JPEG response
```
- Useful for manual testing and verification
- Requires network connectivity
- Slightly higher latency (~1-2 seconds)
- Serialized against BLE-triggered captures via a shared lock, so the two paths can't collide on the camera device

**Path 3: Streaming (Preview Only)** — not yet implemented
```
User accesses /stream → FastAPI starts MJPEG encoder → Live feed streamed
```
- Preview only, not for capture
- Auto-stops on disconnect or timeout
- No resource overhead when not in use

---

## Planned Features

### 1. HTTP API Endpoints

#### `/snapshot` Endpoint ✅ Implemented
- **Purpose**: Fetch a single JPEG image on demand
- **Method**: GET
- **Response**: Raw JPEG data
- **Overhead**: Minimal; no continuous encoding. Overwrites one file (`<output_dir>/web/snapshot.jpg`) rather than adding to the time-lapse archive.
- **Use**: Home Assistant snapshots, manual verification
- **Example**: 
  ```bash
  curl http://raspberrypi.local:8080/snapshot > photo.jpg
  ```

#### `/stream` Endpoint
- **Purpose**: Live MJPEG stream preview
- **Method**: GET
- **Response**: Motion JPEG stream
- **Auto-Timeout**: 300 seconds default (configurable)
- **Behavior**: Stops automatically when client disconnects
- **Resolution**: 640×480 default (configurable per hardware)
- **Frame Rate**: 10-15 fps (Pi Zero 2W optimized)
- **Example**:
  ```html
  <img src="http://raspberrypi.local:8080/stream" width="640" height="480" />
  ```

#### `/capture` Endpoint (Manual Trigger) ✅ Implemented
- **Purpose**: Manually trigger photo capture via web/Home Assistant
- **Method**: POST
- **Response**: JPEG of just-captured image
- **Use**: Testing camera settings, manual verification during setup. Unlike `/snapshot`, this saves into the same numbered `<output_dir>/` sequence as a real Bluetooth-triggered capture.
- **Example**:
  ```bash
  curl -X POST http://raspberrypi.local:8080/capture
  ```

### 2. Web User Interface

A minimal, mobile-friendly web dashboard featuring:
- Live camera preview (MJPEG stream)
- Manual capture button
- Stream start/stop controls
- Last captured timestamp
- Connection status indicator
- Responsive design for phones, tablets, desktops

### 3. Home Assistant Integration

Configure bbl-shutter-cam as a camera entity in Home Assistant:

```yaml
camera:
  - platform: generic
    name: "Printer Camera"
    still_image_url: "http://raspberrypi.local:8080/snapshot"
    stream_source: "http://raspberrypi.local:8080/stream"
    framerate: 12
    verify_ssl: false
```

**Features**:
- Snapshot support for dashboard tiles
- Stream support for live view cards
- Motion detection triggers (if desired)
- Automation integration (if manual capture endpoint added)

### 4. Configuration

New optional `[server]` section in profile config:

```toml
[profiles.my-printer]
# ... existing camera and BLE config ...

[profiles.my-printer.server]
# Optional streaming settings (all with sensible defaults)
web_port = 8080
stream_resolution = "640x480"
stream_fps = 12
stream_timeout_seconds = 300
jpeg_quality = 80
enable_manual_capture = true
```

**All settings are optional** with hardware-aware defaults:
- **Pi 5**: 1080p, 30 fps
- **Pi 4**: 800×600, 20 fps
- **Pi Zero 2W**: 640×480, 12 fps

### 5. Systemd Service (Restored)

The original decision to remove systemd service support is being **reversed** for this feature. A unified service template will support:

```ini
[Service]
ExecStart=/usr/local/bin/bbl-shutter-cam run --profile my-printer --web-port 8080
Type=notify
Restart=on-failure
RestartSec=10
StartLimitInterval=60
StartLimitBurst=3
```

The service provides:
- Auto-restart on crash
- Startup notifications
- Clean systemd integration
- Optional, can still run in foreground for debugging

---

## Resource Requirements

### Memory Footprint (Pi Zero 2W)

| Component | Usage | Notes |
|-----------|-------|-------|
| Python runtime | ~30 MB | Base interpreter |
| FastAPI/uvicorn server | ~15-20 MB | Idle, listening |
| Streaming (active) | ~20 MB | MJPEG encoder — not yet implemented |
| Snapshots | ~5 MB | Per-request, released |
| BLE listener | ~10 MB | Constant |
| **Total idle, measured** | ~50 MB | Whole process (BLE + FastAPI/uvicorn), idle, measured on a Pi 5 running Python 3.13 — not yet measured on a Pi Zero 2W, but within the ~65 MB budget below |
| **Total idle, original estimate** | ~65 MB | 12% of 512 MB RAM |
| **Total streaming** | ~85 MB | 16% of 512 MB RAM — estimate, `/stream` not yet implemented |

### CPU Impact (Pi Zero 2W)

| Scenario | CPU Usage | Throttle Risk |
|----------|-----------|---------------|
| Idle (BLE only) | 1-2% | None |
| Streaming 10 fps | 15-25% | Low |
| Streaming 20 fps | 35-45% | Moderate |
| Capture + stream | 50%+ | High (thermal) |

**Recommendation**: Keep streaming at 10-15 fps on Pi Zero 2W. Capture photos use GPU encoder (minimal CPU impact).

### Network Requirements

- **Snapshot**: 200-400 KB per image (configurable quality)
- **Stream**: 100-200 Kbps at 12 fps @ 640×480
- **Minimum**: 1 Mbps connection recommended
- **LAN only**: Streaming not designed for remote WAN access (security risk)

---

## Safety & Stability Considerations

### Auto-Timeout Design

Streaming stops automatically to prevent resource exhaustion:
- Client disconnect: Stream stops immediately
- No new data consumed for 300 sec: Stream stops automatically
- User closes browser: Stream stops instantly

This prevents accidental resource leaks.

### Single Stream Limitation

Only one client can stream at a time on Pi Zero 2W:
- Second connection request fails gracefully
- User sees "stream in use" message
- First client must terminate for next to connect

This avoids CPU/memory overload.

### Thermal Management

Continuous streaming may trigger CPU throttling on Pi Zero 2W after ~5-10 minutes:
- Normal in enclosure environments (printer heat)
- Auto-timeout prevents sustained throttling
- Bluetooth shutter remains responsive even during throttle
- Consider heatsink or improved ventilation if needed

### Network Security

- **Current**: No authentication (assumes trusted local network)
- **Future**: Optional HTTP Basic Auth in phase 2
- **Recommendation**: Use on local network only; don't expose to internet without authentication
- **Firewall**: Consider UFW rules limiting web port access

---

## Implementation Timeline

### Phase 1 (Immediate) ✅ Done
- [x] Create `streaming.py` module
- [x] Implement `/snapshot` endpoint
- [x] Implement `/capture` endpoint (moved up from later phases — needed for manual/Home Assistant-triggered capture alongside the BLE trigger)
- [x] Build simple HTML web UI
- [x] Add basic server startup in `run` command (`--web-port`)
- [x] Write initial documentation

### Phase 2 (Following)
- [ ] Implement `/stream` with MJPEG encoder
- [ ] Add timeout and auto-cleanup logic
- [ ] Integrate with config system
- [ ] Add Home Assistant integration guide
- [ ] Create troubleshooting docs

### Phase 3 (Future)
- [ ] Optional MQTT support
- [ ] Web-based camera settings UI
- [ ] Historical image gallery
- [ ] Performance metrics dashboard

---

## Comparison: Streaming Technologies

### Why MJPEG (Motion JPEG)?

| Aspect | MJPEG | H.264 | VP8 |
|--------|-------|-------|-----|
| CPU Load | Moderate | High | High |
| Setup Complexity | Simple | Complex | Complex |
| Browser Support | Native | Varies | Varies |
| Latency | ~1-2s | 0.5-1s | 0.5-1s |
| Pi Zero 2W | ✅ Viable | ⚠️ Possible | ❌ Hard |
| Headless Friendly | ✅ Yes | ⚠️ GPU needed | ✅ Yes |
| Quality | Good | Excellent | Good |

**Decision**: MJPEG chosen for simplicity and Pi Zero 2W compatibility. Can revisit if performance requirements change.

---

## Known Limitations & Workarounds

| Limitation | Reason | Workaround |
|-----------|--------|-----------|
| Single stream only | Resource constraint | Use Home Assistant polling of snapshots |
| No authentication (v1) | Network Trust assumption | Use firewall rules, LAN only |
| 10-15 fps max (Zero 2W) | Hardware performance | Monitor, not capture; use BLE for stills |
| No H.264 codec | CPU overhead | MJPEG sufficient for preview use case |
| No persistent video recording | Encoding overhead | Use time-lapse stills + external tools |

---

## Future Enhancements

Potential improvements after initial release:
- MQTT integration for advanced Home Assistant automations
- WebSocket support for lower-latency streaming
- Multi-stream support on Pi 4/5
- H.264 hardware acceleration research
- Remote WAN access with reverse proxy guide
- Performance metrics and monitoring
- Camera parameter tuning via web UI
- Image gallery and archive viewer

---

## Getting Started

```bash
# Install the optional web extra (fastapi + uvicorn)
pip install -e ".[web]"

# Enable the web server on port 8080, alongside the BLE listener
bbl-shutter-cam run --profile my-printer --web-port 8080

# Access the web UI
open http://localhost:8080

# On-demand snapshot (preview, not added to the time-lapse archive)
curl http://raspberrypi.local:8080/snapshot > preview.jpg

# Manually trigger a real capture (saved into the normal output sequence)
curl -X POST http://raspberrypi.local:8080/capture

# In Home Assistant, add to configuration.yaml — snapshot only for now;
# stream_source needs /stream (Phase 2, not yet implemented)
camera:
  - platform: generic
    name: "My Printer"
    still_image_url: "http://raspberrypi.local:8080/snapshot"
```

---

## Related Documentation

- [Interactive Camera Tuning](../user-guide/camera-settings.md) - Optimize image quality (both live and captured)
- [Systemd Service](./systemd-service.md) - Background operation and auto-start
- [Headless Operation](./headless-operation.md) - Running without display
- [Troubleshooting](../troubleshooting.md) - Common issues and solutions
- [Home Assistant Integration](./home-assistant-integration.md) - (Planned docs)

---

## Questions or Feedback?

This is a planned feature. Please share your use cases, hardware constraints, or feature requests via:
- GitHub Issues on the [project repository](https://github.com/bodybybuddha/bbl-shutter-cam)
- Discussions in the README or Contributing guide

Your input helps prioritize and shape the implementation!
