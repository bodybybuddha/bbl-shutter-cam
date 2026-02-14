# Project Roadmap: bbl-shutter-cam

## Overview
This document tracks development releases and features for the bbl-shutter-cam project. The goal is to create a reliable, multi-machine, multi-camera time-lapse capture system using Bambu Lab's BBL_SHUTTER Bluetooth trigger.

---

# Released Versions

## v0.3.1 - Bug Fix Release ✅ Released 2026-02-14

**Milestone:** Fixed default output directory collision between profiles.

### Fixed
- Default output_dir now includes profile name to prevent file collision
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

# Planned Future Development

## Stage 2: Hardware Detection & Multi-Machine Support 📋 Planned (v0.3.0+)

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
- Stage 1 complete ✅

---

## Stage 3: Testing & CI/CD 📋 Planned (v0.3.0+)

### Objectives
- Establish test infrastructure
- Set up automated linting and testing
- Ensure code quality and consistency

### Planned Tasks
- [ ] Create unit tests for `config.py`, `util.py`, `ble.py`
- [ ] Add integration tests for camera module
- [ ] Set up GitHub Actions workflows:
  - Lint (black, pylint, mypy)
  - Test (pytest with coverage)
  - Build (wheel generation)
- [ ] Configure pytest with coverage targets
- [ ] Add test documentation

### Dependencies
- `dev` dependencies must be installed (Stage 1 ✅)

---

## Stage 4: Systemd & Deployment 📋 Planned (v0.3.0+)

### Objectives
- Enable reliable headless operation on Raspberry Pi
- Create deployment templates and documentation

### Planned Tasks
- [ ] Create `bbl-shutter-cam.service` systemd template
- [ ] Add systemd timer for scheduled restarts
- [ ] Document service installation
- [ ] Create systemd user service alternative
- [ ] Add log rotation configuration

### Dependencies
- Requires logging config (Stage 1 ✅)
- Requires hardware detection (Stage 2)

---

## Stage 5: Advanced Documentation & Polish 📋 Planned (v1.0.0)

### Objectives
- Comprehensive user and developer documentation
- Future extensibility guide

### Planned Tasks
- [ ] Write `docs/SETUP.md` (hardware prerequisites, installation)
- [ ] Write `docs/CONFIGURATION.md` (profile management, camera settings)
- [ ] Write `docs/TROUBLESHOOTING.md` (common issues, debug modes)
- [ ] Create `CONTRIBUTING.md` (dev workflow, testing)
- [ ] Create `CHANGELOG.md` (version history)
- [ ] Add hardware-specific guides (Pi Zero 2 W, Pi 4, Pi 5)
- [ ] Create example profiles for common setups

### Dependencies
- All prior stages

---

## Stage 6: Extended Features 📋 Planned (v1.0.0+)

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
- Can integrate with systemd journal in Stage 4

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
| v0.3.0 | 2026-02-14 | Stage 2.6 (Camera Calibration) | ✅ Released |
| v0.2.0 | 2026-02-14 | Stage 1, Stage 2.5 | ✅ Released |
| v0.1.0 | Planning | Initial planning | ✅ Complete |

### Planned Releases

| Version | Target | Planned Stages | Complexity |
|---------|--------|----------------|------------|
| v0.4.0 | TBD | Stage 2 (Hardware Detection), Stage 3 (Testing/CI), Stage 4 (Systemd) | Medium |
| v1.0.0 | TBD | Stage 5 (Documentation Polish), Stage 6 (Extended Features) | High |

---

## Contact & Questions

For progress updates or to discuss upcoming stages, refer to this document and the project's issue tracker.
