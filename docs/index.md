---
layout: page
title: bbl-shutter-cam Documentation
nav_order: 1
permalink: /
---

# bbl-shutter-cam

**Reliable, headless time-lapse capture for Bambu Lab 3D printers on Raspberry Pi.**

## What This Does

`bbl-shutter-cam` listens for Bluetooth shutter signals from a **Bambu Lab CyberBrick Time-Lapse Kit (BBL_SHUTTER)**, automatically captures photos using a Raspberry Pi camera, and stores them locally. Perfect for creating stunning time-lapse videos of your 3D prints directly inside your printer enclosure.

**Key Features:**
- 🎥 Automatic photo capture on shutter triggers
- 🔋 Headless operation (no display needed)
- 🔧 Multi-profile support (multiple printers/cameras)
- 🔍 Intelligent signal discovery (auto-detect unknown Bluetooth signals)
- ⚙️ Extensive camera tuning options (rotation, focus, exposure, white balance, etc.)
- 📝 Configuration-driven (easy to modify settings without code)
- 🛡️ Robust reconnection (handles dropped connections gracefully)

---

## Quick Links

**Getting Started:**
- [Installation & Hardware Requirements](installation/requirements.md)
- [Raspberry Pi Setup](installation/setup-pi.md)
- [Quick Start Guide](user-guide/quick-start.md)

**How To:**
- [Understanding Profiles & Configuration](user-guide/profiles.md)
- [Camera Settings & Tuning](user-guide/camera-settings.md)
- [Discovering Unknown Bluetooth Signals](features/signal-discovery.md)

**Advanced Topics:**
- [Headless Operation](advanced/headless-operation.md)
- [Auto-Start with Systemd](advanced/systemd-service.md)
- [Extending the Application](advanced/extending.md)

**Help:**
- [Troubleshooting Guide](troubleshooting.md)
- [FAQ](faq.md)

---

## Real-World Example

Here's a typical workflow:

### 1. **Setup** (one-time)
```bash
# Install on a Raspberry Pi Zero 2 W with Camera Module 3 NOIR
bbl-shutter-cam setup --profile p1s-office

# System asks you to physically press the shutter button on your CyberBrick
# It learns the Bluetooth signal automatically
```

### 2. **Discover Signals** (if needed)
```bash
# If Bambu Studio app sends different signals, discover them:
bbl-shutter-cam debug --profile p1s-office --duration 120 --update-config

# While the printer is running, Bambu Studio can trigger captures via app
```

### 3. **Tune Camera Settings** (optional, coming in v0.2.0)
```bash
# Adjust rotation, focus, exposure, white balance interactively
bbl-shutter-cam tune --profile p1s-office
```

### 4. **Run for Real**
```bash
# Prints capture automatically as the printer runs
bbl-shutter-cam run --profile p1s-office

# (Or enable systemd auto-start for hands-off operation)
```

### 5. **Review Photos**
```bash
# Access via SFTP or SCP (see Headless Operation guide)
sftp pi@raspberrypi.local
> cd captures/p1s-office
> get *.jpg  # Download all photos
```

---

## System Requirements

**Hardware:**
- Raspberry Pi Zero 2 W, Pi 4, or Pi 5 (Zero 2 W recommended for cost)
- Raspberry Pi Camera Module 3 (Wide-Angle or NOIR variant)
- Bambu Lab CyberBrick Time-Lapse Kit (BBL_SHUTTER)
- 5V power adapter
- SD card (16GB+)

**Software:**
- Raspberry Pi OS Lite (Bookworm recommended)
- Python 3.9+
- `rpicam-still` (included with latest Raspberry Pi OS)

[→ Full hardware guide](installation/requirements.md)

---

## Project Status

**Current Version:** v0.2.0 (Alpha)

### Implemented Features
- ✅ BLE device discovery & setup
- ✅ Manual button press capture (0x4000 signal)
- ✅ Bambu Studio app trigger support (0x8000 signal)
- ✅ Dynamic signal discovery mode (`bbl-shutter-cam debug`)
- ✅ Profile-based configuration
- ✅ Extensive camera options (resolution, rotation, flip, quality settings)
- ✅ Dry-run mode for testing
- ✅ Verbose logging for debugging

### Planned Features (v0.2.0+)
- 🔜 Interactive camera calibration mode (`bbl-shutter-cam tune`)
- 🔜 Systemd service template & auto-start
- 🔜 Unit tests & CI/CD pipelines
- 🔜 Web-based configuration UI

See [ROADMAP.md](../ROADMAP.md) for detailed development timeline.

---

## Getting Help

- **Stuck?** → [Troubleshooting Guide](troubleshooting.md)
- **Common Questions?** → [FAQ](faq.md)
- **Found a bug?** → [GitHub Issues](https://github.com/bodybybuddha/bbl-shutter-cam/issues)
- **Want to contribute?** → [Extending & Contributing](advanced/extending.md)

---

## License

MIT License — See [LICENSE](../LICENSE) file for details.
