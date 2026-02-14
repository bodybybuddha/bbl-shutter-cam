# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.3.0] - 2026-02-14

### Added
- Interactive camera calibration with `bbl-shutter-cam tune` command (Stage 2.6)
- Extended camera configuration support:
  - Focus control: autofocus mode and lens position
  - Color adjustments: saturation, contrast, brightness
  - Advanced settings: metering mode, JPEG quality, timeout
- New `tune.py` module with TuningSession class for interactive settings management
- Test photo capture workflow with automatic numbering and timestamping
- Config save and rollback support in tuning interface
- Headless-friendly interactive menu (works via SSH)

### Changed
- Extended CameraConfig dataclass with 8 additional tunable parameters
- Updated build_rpicam_still_cmd() to support new camera parameters
- Enhanced camera settings documentation with interactive tuning workflow
- Updated example config with all available camera parameters

## [0.2.0] - 2026-02-14

### Added
- Initial alpha release features (BLE device discovery, Bluetooth signal learning, photo capture)
- CLI commands: `scan`, `setup`, `debug`, `run`
- Profile-based configuration system with TOML format
- Multi-printer support via profiles
- Comprehensive documentation and examples with GitHub Pages support
- PyInstaller support for standalone executables (Windows, macOS, Linux)
- VSCode workspace configuration with build/test tasks
- Google-style docstrings for all modules
- Tool configurations for black, pylint, and mypy in pyproject.toml
- Code of Conduct based on Contributor Covenant v2.0
- .editorconfig for cross-IDE formatting consistency
- CHANGELOG.md for semantic versioning tracking

### Fixed
- Git workflow setup (.gitignore configuration for Python projects)
- Documentation structure with Jekyll-compatible GitHub Pages setup

### Changed
- Consolidated Bluetooth setup documentation into dedicated guide

## [0.1.0] - Planning
- Initial project structure and planning
- Repository setup

[0.3.0]: https://github.com/bodybybuddha/bbl-shutter-cam/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/bodybybuddha/bbl-shutter-cam/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/bodybybuddha/bbl-shutter-cam/releases/tag/v0.1.0
