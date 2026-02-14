# Project Roadmap: bbl-shutter-cam

## Overview
This document tracks development releases and features for the bbl-shutter-cam project. The goal is to create a reliable, multi-machine, multi-camera time-lapse capture system using Bambu Lab's BBL_SHUTTER Bluetooth trigger.

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

### Systemd Service (Removed from Roadmap)
While bbl-shutter-cam is designed for headless operation on Raspberry Pi, it does not run as a persistent daemon or background service. The tool operates on-demand when triggered by Bluetooth signals from the printer. A systemd service template was considered but removed from the roadmap as it doesn't align with the tool's event-driven architecture.

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
