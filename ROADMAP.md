# Project Roadmap: bbl-shutter-cam

## Overview
This document tracks development releases and features for the bbl-shutter-cam project. The goal is to create a reliable, multi-machine, multi-camera time-lapse capture system using Bambu Lab's BBL_SHUTTER Bluetooth trigger.

---

# v0.1.0 - Alpha/Foundation Release

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
- systemd service template (deferred to Stage 3)

---

## Stage 2: Hardware Detection & Multi-Machine Support 🔄 In Planning

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
- Requires completion of Stage 1 ✅

---

## Stage 2.5: Dynamic Signal Discovery & Event Configuration 📋 Planned

### Objectives
- Integrate Bluetooth signal discovery into the main application
- Support unknown/vendor-specific BLE trigger signals automatically
- Store discovered signals in profile configuration
- Enable flexible event-to-action mapping

### Planned Tasks
- [ ] Create integrated debug mode (`bbl-shutter-cam debug` or extend `scan`)
  - Option A: Standalone `debug` subcommand
  - Option B: Extend `scan` with `--debug-signals` flag
- [ ] Capture and persist discovered signals:
  - Discover new signal patterns during debug/scan mode
  - Store signal-to-event mapping in config file per profile
  - Update config with previously unseen signals
- [ ] Implement event-based trigger system:
  - Replace hardcoded `PRESS_BYTES` with configurable events
  - Load trigger signals from profile config
  - Support multiple trigger signals per profile
  - Exclude release events by default from photo capture
- [ ] Enhanced event handling:
  - Add `trigger_on_release` option (default: false)
  - Add `capture_on_all_events` option (default: false)
  - Document which events map to which actions
- [ ] Update config schema:
  - Add `[profiles.<name>.device.events]` section
  - Store discovered signals with metadata (first seen, count, etc.)
  - Add event filtering/action configuration options
- [ ] Improve logging:
  - Show which event triggered a capture
  - Log discovered signals during debug mode
  - Provide summary statistics at exit

### Configuration Example
```toml
[profiles.ps1-office.device.events]
# Auto-discovered signals
signals = [
  { hex = "4000", name = "manual_button", capture = true },
  { hex = "8000", name = "bambu_studio", capture = true },
  { hex = "0000", name = "release", capture = false }
]
```

### Dependencies
- Requires debug_ble_traffic.py from v0.1.0 ✅
- Leverages config.py infrastructure (Stage 1 ✅)

---

## Stage 2.6: Interactive Camera Calibration Mode 📋 Planned

### Objectives
- Provide interactive, headless-friendly camera tuning workflow
- Allow users to dial in optimal settings per profile
- Support Raspberry Pi Camera Module 3 NOIR specifics
- Enable iterative photo capture and configuration updates

### Planned Tasks
- [ ] Create `bbl-shutter-cam tune --profile <name>` command
- [ ] Build interactive tuning menu (headless-friendly)
  - Multi-option menu with single-key navigation
  - Show current settings and changes
  - No dependencies on graphical display
- [ ] Implement tuning categories:
  - **Orientation**: Rotation (0/90/180/270), Flip H, Flip V
  - **Focus**: Autofocus mode (auto/manual), Lens position (0.0-1.0)
  - **Exposure & Color**: EV, AWB modes, Saturation, Sharpness
  - **Noise & Speed**: ZSL (enable/disable), Denoise mode
  - **Advanced**: ISO/Gain, Shutter speed, Metering mode
  - **NOIR-Specific**: Low-light boost, IR sensitivity options
- [ ] Capture workflow:
  - Take single test photo with current settings
  - Display file path for manual inspection (headless inspection via SFTP/SCP)
  - Return to menu for adjustments
  - Support batch naming with settings identifier (e.g., `tune_ev0_awb-daylight.jpg`)
- [ ] Configuration integration:
  - Apply settings to camera config dataclass
  - Build rpicam-still command with tuned parameters
  - Save validated settings back to profile config
  - Support rollback to previous settings
- [ ] User guidance:
  - Show recommended settings for NOIR in enclosures
  - Explain each setting's impact on output
  - Suggest starting points based on lighting conditions
  - Document ZSL benefits for timelapse capture

### Configuration Tuning Options

#### Orientation (Essential)
- `rotation`: 0, 90, 180, 270
- `hflip`: true/false
- `vflip`: true/false

#### Focus Control
- `autofocus`: "auto" or "manual"
- `lens_position`: 0.0 (infinity) to 1.0 (closest, ~8cm for Module 3)
- `af_on_capture`: true/false (trigger AF before each shot)

#### Exposure & Color
- `ev`: -10 to +10 (exposure value)
- `awb`: "auto", "daylight", "tungsten", "warm", "cool", "shade"
- `saturation`: 0-2.0 (relative multiplier)
- `sharpness`: 0-2.0 (relative multiplier)

#### Speed & Noise
- `zsl`: true/false (zero shutter lag / buffered capture)
- `denoise`: "off", "fast", "hq"

#### Advanced
- `iso`: 100-800
- `gain`: manual sensor gain value
- `shutter`: microseconds (manual shutter speed)
- `metering`: "center", "spot", "matrix", "custom"

#### NOIR-Specific
- `low_light_boost`: true/false
- `lens_shading`: true/false (correction for edge darkening)

### Configuration Example
```toml
[profiles.ps1-office.camera.rpicam]
width = 1920
height = 1080
nopreview = true
rotation = 0
hflip = false
vflip = false

# ZSL for faster, more reliable timelapse
zsl = true
denoise = "hq"

# Focus locked for consistent captures
autofocus = "manual"
lens_position = 0.5

# Color & Exposure
ev = 0
awb = "daylight"
saturation = 1.0
sharpness = 0.5

# NOIR Camera optimizations
low_light_boost = true
metering = "matrix"
```

### Interactive Menu Example (Headless)
```
=== Camera Calibration: ps1-office ===
Last photo: /home/pi/captures/ps1-office/tune_001.jpg

CURRENT SETTINGS:
  Rotation: 0°      HFlip: No      VFlip: No
  Focus: manual     Pos: 0.5       LowLight: Yes
  EV: 0             AWB: daylight  Denoise: hq
  ZSL: enabled      Saturation: 1.0

ADJUST SETTINGS:
  [R]otation | [H/V]flip | [F]ocus [P]osition | [E]V
  [A]WB | [Sa]turation | [Sh]arpness | [D]enoise | [Z]SL
  [L]ow-light | [Me]tering

ACTIONS:
  [T]ake photo | [C]ompare settings | [Sa]ve & exit | [Q]uit

Choose option: _
```

### Dependencies
- Requires camera.py module (Stage 1 ✅)
- Requires config.py update (Stage 1 ✅)
- Can run independently or after Stage 2.5

---

# Future Versions

## Stage 3: Testing & CI/CD 📋 Planned

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

## Stage 4: Systemd & Deployment 📋 Planned

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

## Stage 5: Documentation & Polish 📋 Planned

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

## Stage 6: Extended Features 📋 Planned

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

## v0.1.0 Release Status

| Stage | Complexity | Est. Time | Status |
|-------|-----------|-----------|--------|
| 1 (Foundation) | Low | ✅ Complete | ✅ Done |
| 2 (Hardware Detect) | Medium | 2-3 days | 🔄 In Progress |

**Target Release**: When Stage 2 is complete

---

## Future Release Timeline

| Stage | Complexity | Est. Time | Target |
|-------|-----------|-----------|--------|
| 2.5 (Signal Discovery) | Medium | 3-4 days | v0.2.0 |
| 2.6 (Camera Calibration) | Medium | 3-4 days | v0.2.0 |
| 3 (Testing & CI/CD) | Medium | 3-4 days | v0.2.0 |
| 4 (Systemd) | Low-Medium | 1-2 days | v0.2.0 or later |
| 5 (Documentation) | Low | 2-3 days | v0.2.0 or later |
| 6 (Extended Features) | High | 1-2 weeks | v1.0.0+ |

---

## Contact & Questions

For progress updates or to discuss upcoming stages, refer to this document and the project's issue tracker.
