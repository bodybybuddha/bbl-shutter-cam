# Project Roadmap: bbl-shutter-cam

## Overview
This document tracks development releases and features for the bbl-shutter-cam project. The goal is to create a reliable, multi-machine, multi-camera time-lapse capture system using Bambu Lab's BBL_SHUTTER Bluetooth trigger.

## Release Process (Standard)

Use the following checklist to keep releases consistent and reproducible:

- All feature/bugfix work lands in `dev` via PRs (no direct commits to `dev`/`main`).
- Create a release PR from `dev` → `main`.
- Update documentation and examples as part of the release PR when applicable:
  - `CHANGELOG.md` (new version section; follow SemVer)
  - `README.md` and any relevant `docs/` pages
  - `examples/config.example` and `examples/config.minimal.toml` (if config changed)
  - `ROADMAP.md` (mark milestone complete / adjust upcoming items)
- Ensure CI is green on the release PR.
- Merge the release PR.
- Create a tag/release on `main` (tags/releases should point at `main`).
- Verify release artifacts (Pi binaries) are attached and runnable.

---

# Released Versions

## v1.0.0 - Production Release ✅ Released 2026-02-14

**Milestone:** Production-ready release with CI, expanded tests, and documentation polish.

### Completed Features
- ✅ GitHub Actions CI for lint, type check, and tests (Python 3.9-3.13)
- ✅ Test coverage target enforced at 80%
- ✅ Expanded unit test coverage across BLE, CLI, discover, tune, and logging
| v1.0.0 | 2026-02-14 | Stage 3, Stage 5 | ✅ Released |
- ✅ Release workflow builds Raspberry Pi binaries (arm64 + armv7)
- ✅ Documentation refresh for v1.0.0 and release artifacts

### Stages Completed in v1.0.0
- Stage 3: Testing & CI/CD
### Planned Releases

| Version | Target | Planned Stages | Complexity |
|---------|--------|----------------|------------|
| TBD | TBD | Post-v1 features (Hardware Detection, Extended Features) | Medium |
- Profiles without explicit `output_dir` setting now default to `~/captures/{profile_name}/`

---

## v0.3.0 - Interactive Camera Tuning ✅ Released 2026-02-14

**Milestone:** Added interactive camera calibration for optimal image quality.

### Completed Features
- ✅ Interactive camera tuning with `bbl-shutter-cam tune` command
- ✅ Headless-friendly menu system (SSH compatible)
- ✅ Test photo capture with automatic numbering
- ✅ Extended camera parameter support (focus, color, metering, quality)
- ✅ Configuration save and rollback functionality
- ✅ Comprehensive tuning documentation

### Stages Completed in v0.3.0
- Stage 2.6: Interactive Camera Calibration Mode

---

## v0.2.0 - Alpha Release ✅ Released 2026-02-14

**Milestone:** First functional alpha release with core features complete.

### Completed Features
- ✅ BLE device discovery and pairing
- ✅ Profile-based configuration system (TOML)
- ✅ Multi-printer/multi-camera support
- ✅ Dynamic signal discovery and auto-config updates
- ✅ Event-based trigger system (configurable capture events)
- ✅ Photo capture with rpicam-still integration
- ✅ Comprehensive documentation with GitHub Pages
- ✅ PyInstaller executable support (Windows, macOS, Linux)
- ✅ CLI commands: `scan`, `setup`, `debug`, `run`
- ✅ VSCode workspace configuration
- ✅ Development tooling (black, pylint, mypy, pytest)

### Stages Completed in v0.2.0
- Stage 1: Foundation & Setup
- Stage 2.5: Dynamic Signal Discovery & Event Configuration

---

# Development History

## v0.1.0 - Planning & Foundation

## Stage 1: Foundation & Setup ✅ Complete

### Objectives
- Establish project structure following Python best practices
- Set up development environment tooling
- Create documentation foundation

### Completed Tasks
- ✅ Created virtual environment (.venv)
- ✅ Installed project dependencies with pinned versions (0.22.x, 0.12.x)
- ✅ Added `.gitignore` with Python/IDE/project-specific patterns
- ✅ Updated `pyproject.toml`:
  - Added dev dependencies (pytest, black, pylint, mypy)
  - Added Python 3.9+ classifiers
  - Fixed GitHub repository URLs
  - Pinned dependency versions to minor releases
- ✅ Created directory structure:
  - `tests/` for unit and integration tests
  - `docs/` for documentation
  - `.github/workflows/` for CI/CD pipelines
- ✅ Added MIT LICENSE file
- ✅ Created `logging_config.py` module for enhanced logging capabilities

### Not Yet Implemented
- systemd service template (deferred to Stage 4)

---

## Stage 2.5: Dynamic Signal Discovery & Event Configuration ✅ Complete (v0.2.0)

### Objectives
- Integrate Bluetooth signal discovery into the main application
- Support unknown/vendor-specific BLE trigger signals automatically
- Store discovered signals in profile configuration
- Enable flexible event-to-action mapping

### Completed Tasks
- ✅ Created standalone `debug` subcommand with full signal capture
- ✅ Capture and persist discovered signals:
  - Discover new signal patterns during debug mode
  - Store signal-to-event mapping in config file per profile
  - Auto-update config with `--update-config` flag
- ✅ Implemented event-based trigger system:
  - Replaced hardcoded `PRESS_BYTES` with configurable events
  - Load trigger signals from profile config
  - Support multiple trigger signals per profile
  - Exclude release events (0x0000) by default from photo capture
- ✅ Enhanced event handling:
  - Event capture flag per signal (`capture: true/false`)
  - Load events dynamically from `device.events` config section
  - Support for backward compatibility with defaults
- ✅ Updated config schema:
  - Added `[profiles.<name>.device.events]` array
  - Store discovered signals with metadata (uuid, hex, count, capture flag)
  - Event filtering via capture boolean
- ✅ Improved logging:
  - Show which event triggered a capture (by name or hex)
  - Log discovered signals during debug mode with timestamps
  - Provide detailed summary statistics at exit with signal counts

### Implemented Configuration Example
```toml
# Auto-discovered and stored in profile
[[profiles.ps1-office.device.events]]
uuid = "00002a4d-0000-1000-8000-00805f9b34fb"
hex = "4000"
count = 5
capture = true

[[profiles.ps1-office.device.events]]
uuid = "00002a4d-0000-1000-8000-00805f9b34fb"
hex = "8000"
count = 3
capture = true

[[profiles.ps1-office.device.events]]
uuid = "00002a4d-0000-1000-8000-00805f9b34fb"
hex = "0000"
count = 8
capture = false
```

### Implementation Details
- Implemented in `discover.py::debug_signals()` and `discover.py::_update_config_with_signals()`
- Config helpers in `config.py::get_trigger_events()` and `config.py::get_event_trigger_bytes()`
- Full documentation at `docs/features/signal-discovery.md`
- CLI integration via `cli.py::_cmd_debug()`

---

## Stage 2.6: Interactive Camera Calibration Mode ✅ Complete (v0.4.0)

### Objectives
- Provide interactive, headless-friendly camera tuning workflow
- Allow users to dial in optimal settings per profile
- Support Raspberry Pi Camera Module 3 NOIR specifics
- Enable iterative photo capture and configuration updates

### Completed Tasks
- ✅ Created `bbl-shutter-cam tune --profile <name>` command
- ✅ Built interactive tuning menu (headless-friendly)
  - Multi-option menu with single-key navigation
  - Show current settings and changes  - No dependencies on graphical display
- ✅ Implemented tuning categories:
  - **Orientation**: Rotation (0/90/180/270), Flip H, Flip V
  - **Focus**: Autofocus mode (auto/manual/continuous), Lens position (0.0-32.0)
  - **Exposure & Color**: EV, AWB modes, Saturation, Contrast, Brightness, Sharpness
  - **Noise & Quality**: Denoise mode, JPEG quality
  - **Advanced**: Shutter speed, Gain, Metering mode
- ✅ Capture workflow:
  - Take single test photo with current settings
  - Display file path for manual inspection (headless inspection via SFTP/SCP)
  - Return to menu for adjustments
  - Batch naming with counter and timestamp
- ✅ Configuration integration:
  - Apply settings to camera config dataclass
  - Build rpicam-still command with tuned parameters
  - Save validated settings back to profile config
  - Support rollback to original settings

### Implementation Details
- New module: `tune.py` with `TuningSession` class
- Extended `CameraConfig` dataclass with all tunable parameters
- Updated `build_rpicam_still_cmd()` to support new parameters
- CLI integration via `cli.py::_cmd_tune()`
- Test photos saved to `<output_dir>/tune/` subdirectory
- Updated documentation in `docs/user-guide/camera-settings.md`
- Extended example config with all tunable parameters

---

# v1.0.0 Completion Details

## Stage 3: Testing & CI/CD ✅ Complete (v1.0.0)

### Objectives
- Establish test infrastructure
- Set up automated linting and testing
- Ensure code quality and consistency

### Completed Tasks
- ✅ Create unit tests for `config.py`, `util.py`, `ble.py`, `discover.py`, `tune.py`, `cli.py`
- ✅ Add integration coverage for camera module utilities
- ✅ Set up GitHub Actions workflows:
  - Lint (black, pylint, mypy)
  - Test (pytest with coverage)
  - Release build (PyInstaller for Raspberry Pi)
- ✅ Configure pytest with coverage targets (80% gate)
- ✅ Add test documentation in CONTRIBUTING

### Dependencies
- `dev` dependencies must be installed (Stage 1 ✅)

---

## Stage 5: Documentation & Polish ✅ Complete (v1.0.0)

### Objectives
- Comprehensive user and developer documentation
- Production-ready documentation and examples

### Completed Tasks
- ✅ Updated docs index and quick start for v1.0.0
- ✅ Updated `CONTRIBUTING.md` with dev workflow and CI/test guidance
- ✅ Documented Raspberry Pi setup and requirements
- ✅ Provided example profiles and configuration templates
- ✅ Documented release artifacts and build process
- ✅ Polished existing documentation for clarity and completeness

### Dependencies
- All prior stages

---

# Post-v1.0.0 Features

## Future: Hardware Detection & Multi-Machine Support 📋 Planned (Post-v1)

### Objectives
- Implement automatic hardware detection (Pi model, camera type)
- Create setup wizard for first-run configuration
- Support multi-camera and multi-printer profiles

### Planned Tasks
- [ ] Detect Raspberry Pi hardware (model, OS version)
- [ ] Detect camera type (rpicam, picamera, etc.)
- [ ] Build interactive setup wizard
- [ ] Validate config against detected hardware
- [ ] Create hardware-specific presets
- [ ] Document multi-machine deployment patterns

### Dependencies
- v1.0.0 release complete

---

## Stage 4: Web Streaming & Home Assistant Integration 📋 Planned (Post-v1)

### Objectives
- Add optional web-based live streaming capability for remote monitoring
- Enable Home Assistant integration for camera feeds and remote control
- Maintain lightweight operation on constrained devices (Raspberry Pi Zero 2W)
- Preserve Bluetooth shutter as primary reliable trigger for time-lapse capture
- Restore systemd service functionality for long-running operation

### Key Design Principles
- **Non-intrusive**: Streaming is optional and disabled by default
- **On-demand**: Stream only starts when endpoint is accessed; stops on client disconnect
- **Resource-aware**: MJPEG streaming at modest resolution (640×480) for Pi Zero 2W compatibility
- **Single process**: Web server runs alongside BLE listener in same systemd service
- **Dual capture paths**:
  - Primary: Bluetooth shutter trigger → rpicam-still (clean time-lapse sequences)
  - Secondary: Manual triggers via web UI + streaming preview

### Planned Implementation

#### Core Features
- [ ] **HTTP API Server** (Flask or FastAPI)
  - `/snapshot` endpoint: Single JPEG image on demand (zero encoding overhead)
  - `/stream` endpoint: On-demand MJPEG stream with configurable timeout (default 300s)
  - Stream auto-stops on client disconnect or timeout
  - Low-power operation between requests
  
- [ ] **Web UI** (minimal HTML/JS)
  - Live preview window showing MJPEG stream
  - Manual snapshot button for captured stills
  - Stream start/stop controls
  - Connection status indicator

- [ ] **Home Assistant Integration**
  - Camera entity with configurable stream URL
  - Snapshot support for dashboards
  - Optional manual trigger endpoint (if desired)
  - MQTT support for advanced integrations (optional phase 2)

- [ ] **Systemd Service Restoration**
  - Unified service running BLE listener + web server
  - New CLI flag `--web-port [PORT]` to enable streaming (default: disabled)
  - Example: `bbl-shutter-cam run --profile my-printer --web-port 8080`
  - Service remains daemonizable via systemd (reverts decision from post-v1.0.0 notes)

- [ ] **Configuration Updates**
  - Optional `[server]` section in profile config for streaming settings
  - Configurable stream resolution, quality, timeout, and idle behavior
  - Default presets for different hardware tiers (Pi 5, Pi 4, Pi Zero 2W)

#### Technical Specifications

**Stream Architecture:**
- MJPEG protocol (Motion JPEG) for compatibility and low CPU overhead
- libcamera/picamera2 native streaming where possible
- Single concurrent stream maximum (Pi Zero 2W resource constraint)
- Graceful fallback if stream unavailable

**Performance Targets (Pi Zero 2W):**
- Stream resolution: 640×480 default
- Frame rate: 10-15 fps (acceptable for preview)
- Latency: <2 seconds first frame
- Memory overhead: <50 MB for web server
- CPU overhead: <10% at idle, <40% when streaming

**Home Assistant Integration:**
- Native camera entity config via YAML
- Auto-discovery via MQTT (optional)
- Manual URL entry as fallback
- Support for snapshot + stream URLs for flexible HA deployments

### Planned Tasks
- [ ] Create `streaming.py` module (web server + stream handlers)
- [ ] Add Flask/Werkzeug dependencies to `pyproject.toml`
- [ ] Extend `CameraConfig` dataclass with stream settings
- [ ] Update `cli.py` to support `--web-port` flag on `run` command
- [ ] Integrate Flask server with existing BLE listener in main loop
- [ ] Build minimal HTML template for web UI
- [ ] Create on-demand MJPEG generator with timeout logic
- [ ] Add `/snapshot` and `/stream` endpoint handlers
- [ ] Update config schema with `[server]` section examples
- [ ] Write comprehensive Home Assistant integration guide
- [ ] Document stream architecture and resource usage
- [ ] Add integration tests for streaming endpoints
- [ ] Update systemd service template with streaming examples
- [ ] Create troubleshooting guide for streaming connectivity issues

### Configuration Examples

**Enable streaming with defaults:**
```toml
[profiles.my-printer]
# ... existing config ...

# Optional: customize stream settings
[profiles.my-printer.server]
web_port = 8080
stream_resolution = "640x480"
stream_fps = 12
stream_timeout_seconds = 300
jpeg_quality = 80
```

**Home Assistant YAML configuration:**
```yaml
camera:
  - platform: generic
    name: "Printer Timelapse"
    still_image_url: "http://raspberrypi.local:8080/snapshot"
    stream_source: "http://raspberrypi.local:8080/stream"
    framerate: 12
```

### Dependencies
- v1.0.0 release complete
- Hardware detection stage (if sequenced after)
- System: Flask or FastAPI, Python 3.9+
- Camera: libcamera/picamera2 with streaming support

### Phase Planning
- **Phase 1** (immediate): `/snapshot` endpoint, basic web UI
- **Phase 2** (following): On-demand MJPEG streaming with timeout
- **Phase 3**: Full Home Assistant integration docs + MQTT support

### Testing Strategy
- Unit tests for stream handlers and timeout logic
- Integration tests for endpoint accessibility and resource cleanup
- Manual testing on Pi Zero 2W to verify resource footprint
- Documentation of expected behavior on different hardware tiers

### Considerations & Risks
- **MJPEG vs H.264**: Prioritized MJPEG for CPU simplicity; can revisit if needed
- **Concurrent streams**: Limiting to 1 stream to avoid resource exhaustion
- **Network bandwidth**: User responsible for network capacity; guide provided
- **Security**: Initial version assumes trusted network; add auth in phase 2 if needed
- **Thermal**: Continuous streaming may trigger Pi Zero 2W throttling; timeout mitigates

---

## Future: Extended Features 📋 Planned (Post-v1)

### Objectives
- Enhance core functionality based on user feedback

### Potential Features
- [ ] Multi-camera simultaneous capture
- [ ] Remote trigger via HTTP API
- [ ] Photo gallery/viewer
- [ ] Email notifications on error
- [ ] Backup to cloud storage
- [ ] Web-based configuration UI
- [ ] Performance metrics/stats

---

## Notes

### Version Pinning Strategy
- **Runtime deps**: `>=X.Y,<X+1` (minor version constraints)
- **Dev deps**: Same convention for consistency
- Ensures compatibility across machines while allowing patch updates

### Logging Configuration
- Centralized in `logging_config.py`
- Supports colored terminal output for development
- File logging with rotation for production/headless
- Compatible with existing `util.py` LOG infrastructure

### Systemd Service
While bbl-shutter-cam was initially designed as an event-driven tool without persistent daemon functionality, restoring systemd service capability is planned in Stage 4 (Web Streaming). This will allow the tool to run as a background service alongside streaming functionality when configured with `--web-port`. For headless time-lapse operation without streaming needs, the tool continues to operate on-demand as per the original design.

### Multi-Machine Deployment
- User configs stored in `~/.config/bbl-shutter-cam/config.toml`
- Hardware detection ensures settings match target device
- Profiles support different printer/camera combinations
- Logging to `~/.log/` for easy troubleshooting across machines

---

## Release Timeline

### Completed Releases

| Version | Date | Stages Completed | Status |
|---------|------|------------------|--------|
| v1.0.0 | 2026-02-14 | Stage 3, Stage 5 | ✅ Released |
| v0.3.1 | 2026-02-14 | Bug Fix (output_dir default) | ✅ Released |
| v0.3.0 | 2026-02-14 | Stage 2.6 (Camera Calibration) | ✅ Released |
| v0.2.0 | 2026-02-14 | Stage 1, Stage 2.5 | ✅ Released |
| v0.1.0 | Planning | Initial planning | ✅ Complete |

### Planned Releases

| Version | Target | Planned Stages | Complexity |
|---------|--------|----------------|------------|
| TBD | TBD | Post-v1 features (Hardware Detection, Extended Features) | Medium |

### Post-v1.0.0 Development

Future enhancements (Hardware Detection, Extended Features) will be planned after v1.0.0 based on user feedback and requirements.

---

## Contact & Questions

For progress updates or to discuss upcoming stages, refer to this document and the project's issue tracker.
