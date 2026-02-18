# bbl-shutter-cam

Use a **Bambu Lab CyberBrick / BBL_SHUTTER Bluetooth shutter** to trigger photos on a **Raspberry Pi** using `rpicam-still`.

**Perfect for:** Headless, reliable time-lapse capture inside 3D printer enclosures with support for multiple printers/cameras through profile-based configuration.

![Status Badge](https://img.shields.io/badge/Status-Stable-brightgreen)
![License](https://img.shields.io/badge/License-MIT-green)
[![Lint](https://github.com/bodybybuddha/bbl-shutter-cam/actions/workflows/lint.yml/badge.svg)](https://github.com/bodybybuddha/bbl-shutter-cam/actions/workflows/lint.yml)
[![Test](https://github.com/bodybybuddha/bbl-shutter-cam/actions/workflows/test.yml/badge.svg)](https://github.com/bodybybuddha/bbl-shutter-cam/actions/workflows/test.yml)
[![GitHub Release](https://img.shields.io/github/release/bodybybuddha/bbl-shutter-cam.svg?style=flat)](https://github.com/bodybybuddha/bbl-shutter-cam/releases)

---

## What This Does

- 🎥 **BLE Listening** - Pairs with BBL_SHUTTER and listens for shutter signals
- 📸 **Auto Capture** - Triggers `rpicam-still` on each press (configurable)
- 🔧 **Multi-Printer** - Manage multiple printers/cameras with profiles
- 🎛️ **Interactive Tuning** - Dial in camera settings interactively
- 🔋 **Headless** - Runs without GUI; optional systemd auto-start
- 📝 **Config-Driven** - TOML profiles for easy setup and tweaking
- 🎯 **Smart Debounce** - Prevents accidental double-triggers
- 📊 **Signal Discovery** - Auto-detect unknown BLE triggers

---

## Quick Start

### 1. Install System Dependencies

```bash
sudo apt update && sudo apt install -y \
  bluetooth bluez libcamera-apps
```

### 2. Install bbl-shutter-cam

**Option A: Standalone Executable (Recommended - easiest, no Python needed)**

1. Download the latest release from [GitHub Releases](https://github.com/bodybybuddha/bbl-shutter-cam/releases)
2. Choose the correct ARM binary for your Pi:
   - **64-bit (most common)**: `bbl-shutter-cam-<version>-linux-arm64`
   - **32-bit older Pi**: `bbl-shutter-cam-<version>-linux-armv7`

3. Make it executable and install:
```bash
# Option 1: System-wide installation (requires sudo)
chmod +x bbl-shutter-cam-<version>-linux-arm64
sudo mv bbl-shutter-cam-<version>-linux-arm64 /usr/local/bin/bbl-shutter-cam
bbl-shutter-cam --help

# Option 2: User installation (no sudo required)
mkdir -p ~/.local/bin
chmod +x bbl-shutter-cam-<version>-linux-arm64
mv bbl-shutter-cam-<version>-linux-arm64 ~/.local/bin/bbl-shutter-cam
export PATH="$HOME/.local/bin:$PATH"
bbl-shutter-cam --help
```

**Option B: From Source (for developers or custom modifications)**

```bash
# Install Python development tools first
sudo apt install -y python3 python3-venv python3-pip

# Clone and install
git clone https://github.com/bodybybuddha/bbl-shutter-cam.git
cd bbl-shutter-cam
python3 -m venv .venv && source .venv/bin/activate
pip install -e .
bbl-shutter-cam --help
```

### 3. Pair Your Device

[Complete Bluetooth setup guide →](https://bodybybuddha.github.io/bbl-shutter-cam/installation/bluetooth-setup.html)

Quick overview:
```bash
sudo bluetoothctl
# power on
# agent on
# scan on
# [wait for BBL_SHUTTER]
# pair AA:BB:CC:DD:EE:FF
# trust AA:BB:CC:DD:EE:FF
# quit

# Note: paired shutters may sleep and not appear in scans.
# Press the shutter button to wake it before scanning or setup.
```

### 4. Configure & Run

```bash
# Setup first time (learns shutter signal)
bbl-shutter-cam setup --profile my-printer

# Tune camera settings interactively (optional)
bbl-shutter-cam tune --profile my-printer

# Test (no photos taken)
bbl-shutter-cam run --profile my-printer --dry-run --verbose

# Run for real
bbl-shutter-cam run --profile my-printer
```

Photos save to `~/.config/bbl-shutter-cam/config.toml` output directory.

---

## Documentation

**Installation & Setup:**
- [Hardware & Software Requirements](https://bodybybuddha.github.io/bbl-shutter-cam/installation/requirements.html)
- [Bluetooth Setup Detailed Guide](https://bodybybuddha.github.io/bbl-shutter-cam/installation/bluetooth-setup.html)
- [Raspberry Pi System Setup](https://bodybybuddha.github.io/bbl-shutter-cam/installation/setup-pi.html)

**Using bbl-shutter-cam:**
- [Quick Start Guide](https://bodybybuddha.github.io/bbl-shutter-cam/user-guide/quick-start.html)
- [Profiles & Configuration](https://bodybybuddha.github.io/bbl-shutter-cam/user-guide/profiles.html)
- [Camera Settings & Tuning](https://bodybybuddha.github.io/bbl-shutter-cam/user-guide/camera-settings.html)
- [Signal Discovery](https://bodybybuddha.github.io/bbl-shutter-cam/features/signal-discovery.html)

**Advanced:**
- [Headless Operation & Systemd](https://bodybybuddha.github.io/bbl-shutter-cam/advanced/headless-operation.html)
- [Building Standalone Executables](https://bodybybuddha.github.io/bbl-shutter-cam/advanced/building-executables.html)
- [Code Architecture & Extending](https://bodybybuddha.github.io/bbl-shutter-cam/advanced/extending.html)

**Help:**
- [Troubleshooting](https://bodybybuddha.github.io/bbl-shutter-cam/troubleshooting.html)
- [FAQ](https://bodybybuddha.github.io/bbl-shutter-cam/faq.html)

---

## Features & Configuration

### Profiles

Multiple printer setups via named profiles:

```bash
bbl-shutter-cam setup --profile p1s-office
bbl-shutter-cam setup --profile p1s-workshop
bbl-shutter-cam run --profile p1s-office
```

### Camera Options

- Resolution (width, height)
- Rotation (0°/90°/180°/270°)
- Flip (horizontal, vertical)
- Exposure (EV compensation, shutter speed, manual gain)
- White balance (auto, daylight, tungsten, custom gains)
- Denoising, sharpness, and other rpicam-still options

See [Camera Settings](https://bodybybuddha.github.io/bbl-shutter-cam/user-guide/camera-settings.html) for all options.

### Signal Discovery

Auto-detect new trigger signals:

```bash
bbl-shutter-cam debug --profile my-printer --duration 120 --update-config
```

Captures all BLE signals while you trigger the shutter or Bambu Studio app and saves them to config.

---

## Tips & Best Practices

- **BLE Connection Issues?** Press the shutter button to wake the device
- **Prevent Double Captures?** Adjust `min_interval_sec` in camera config (default: 0.5s)
- **Varying Enclosure Lighting?** Lock exposure with manual `shutter` and `gain` settings
- **Headless Setup?** Use `--log-file` for debugging on remote systems
- **Auto-Start on Boot?** Optional [Systemd Service](https://bodybybuddha.github.io/bbl-shutter-cam/advanced/systemd-service.html) helps ensure the tool is always listening

---

## Contributing

Want to help? See [CONTRIBUTING.md](CONTRIBUTING.md) for:
- Development setup
- Code style & testing
- VSCode workspace configuration
- Submitting changes

Quick start for developers:
```bash
pip install -e ".[dev]"
python -m pytest tests/ -v          # Run tests
./scripts/build.sh                  # Build executable
```

---

## License & Status

**License:** MIT (see [LICENSE](LICENSE))

**Status:** Stable - v1.0.0 release

**Roadmap:** See [ROADMAP.md](ROADMAP.md) for planned features:
- Hardware detection & interactive setup wizard (Stage TBD)
- **Web streaming & Home Assistant integration** - Live preview and remote monitoring (Stage 4, planned post-v1)
  - Optional `/snapshot` and `/stream` HTTP endpoints
  - Lightweight on Pi Zero 2W (MJPEG @ 640×480, 10-15 fps)
  - Home Assistant camera entity integration
  - Smartphone-friendly web UI
  - See [Web Streaming Documentation](https://bodybybuddha.github.io/bbl-shutter-cam/advanced/web-streaming.html) for details
- Multi-machine CLI and config management (future)

---

## GitHub

- **Repository:** https://github.com/bodybybuddha/bbl-shutter-cam
- **Issues & Bugs:** [GitHub Issues](https://github.com/bodybybuddha/bbl-shutter-cam/issues)

---

## System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| **Raspberry Pi** | Pi 3B+ | Pi Zero 2 W or Pi 5 |
| **OS** | Bullseye | Bookworm (Lite) |
| **Python** | 3.9 | 3.11+ |
| **Camera** | libcamera compatible | Pi Camera Module 3 |
| **Bluetooth** | Built-in/USB adapter | Built-in module |

See [Requirements](https://bodybybuddha.github.io/bbl-shutter-cam/installation/requirements.html) for full details.

