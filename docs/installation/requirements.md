---
layout: page
title: Hardware & Software Requirements
nav_order: 2
parent: Installation
---

# Hardware & Software Requirements

## Hardware

### Raspberry Pi (Required)

**Recommended: Raspberry Pi Zero 2 W**
- Most cost-effective option
- Sufficient processing power for time-lapse capture
- Compact size (perfect for printer enclosures)
- Price: ~$15 USD
- For details, see [Raspberry Pi Comparison](#raspberry-pi-comparison)

### Camera Module (Required)

**Recommended: Raspberry Pi Camera Module 3 NOIR Wide-Angle**
- **NOIR variant**: Better for low-light environments (important in enclosed printer spaces)
- **Wide-angle lens**: Captures more of the print bed
- **Module 3 specifics**: Superior autofocus, faster capture
- Alternatives: Module v2, HQ camera (wider compatibility but fewer optimizations)

### CyberBrick / BBL_SHUTTER (Required)

- **Bambu Lab CyberBrick Time-Lapse Kit**
- Must include the **BBL_SHUTTER** Bluetooth button/sensor
- Firmware version: Recent (tested with 2024+ firmware)
- Signal compatibility: Manual button press (0x4000), Bambu Studio app (0x8000)

### Power & Connectivity

- **Power**: 5V, 2A USB-C power adapter (e.g., Raspberry Pi official 5W+ supply)
- **Storage**: microSD card, 16GB+ (U3 speed class recommended)
- **Network**: Optional Ethernet/WiFi (for remote access, log review)
- **Cables**: USB-C power, microSD adapter (usually included with Pi)

### Mounting & Enclosure

- **Camera mounting**: Flexible gooseneck or fixed bracket
- **Pi mounting**: Clip mount or adhesive strips (3M VHB recommended)
- **Positioning**: Camera should view print bed at slight angle, protected from heat/plastic spatter
- **Cooling**: Ensure adequate ventilation; avoid direct heat from printer

### Estimated Cost

| Component | Cost | Notes |
|-----------|------|-------|
| Raspberry Pi Zero 2 W | ~$15 | Most affordable |
| Camera Module 3 NOIR | ~$30 | Best for dark enclosures |
| CyberBrick Kit | ~$20–40 | Prices vary by region |
| Power supply | ~$5–10 | Reuse if available |
| microSD card | ~$5–15 | 16GB, fast speeds |
| Cables/Mounts | ~$5–15 | Optional accessories |
| **Total** | **~$80–120** | Complete starter kit |

### Alternative Pi Options

#### Pi Zero 2 W (Recommended)
- **Pros**: Cheapest, smallest, sufficient for time-lapse
- **Cons**: Slower CPU (noticeably if running other services)
- **Best for**: Dedicated time-lapse capture, single printer

#### Pi 4 (2GB+)
- **Pros**: 4× faster CPU, room for expansion, better for multi-profile
- **Cons**: Larger, higher power draw, $40+
- **Best for**: Multiple printers, concurrent operations

#### Pi 5
- **Pros**: Latest performance, future-proof
- **Cons**: Expensive ($60+), overkill for time-lapse
- **Best for**: Hobbyists wanting latest hardware

---

## Software Requirements

### Raspberry Pi OS

**Recommended: Raspberry Pi OS Lite (Bookworm)**
- Lightweight (no desktop/GUI needed)
- Latest kernel & drivers
- Pre-installed `rpicam-still` (modern camera framework)
- ~300MB download, ~2GB installed

**Installation:**
1. Download [Raspberry Pi Imager](https://www.raspberrypi.com/software/)
2. Select: Raspberry Pi Zero 2 W → Raspberry Pi OS Lite (Bookworm)
3. Configure: WiFi, hostname, username/password
4. Write to microSD and boot

### Python 3.9+

Raspberry Pi OS Bookworm ships with **Python 3.11** ✅

**Verify installation:**
```bash
python3 --version
# Python 3.11.2
```

### rpicam-still

Modern Raspberry Pi OS includes this by default.

**Verify:**
```bash
which rpicam-still
# /usr/bin/rpicam-still
```

**If missing (older OS)**, install:
```bash
sudo apt update
sudo apt install -y libraspberrypi-bin
```

### Project Dependencies

`bbl-shutter-cam` requires:
```
bleak>=0.22.0,<0.23     # Bluetooth LE client
tomlkit>=0.12.0,<0.13   # TOML config parsing
```

**Installed automatically** during setup (see [Quick Start](../user-guide/quick-start.md)).

---

## Bluetooth / BLE Requirements

### Hardware Support
- **Raspberry Pi Zero 2 W**: ✅ Built-in Bluetooth 5.0
- **Pi 4/5**: ✅ Built-in Bluetooth
- **Older Pi models**: May need external USB Bluetooth adapter

**Test Bluetooth:**
```bash
sudo hcitool scan
# Shows nearby Bluetooth devices (should find your CyberBrick)
```

### CyberBrick Pairing

- **Automatic**: `bbl-shutter-cam setup` discovers and uses the device by name
- **No password**: CyberBrick uses standard Bluetooth LE (no PIN needed)
- **Range**: ~10–50 meters line-of-sight (indoors, ~10m typical)

---

## Optional: System-Level Setup

For **headless operation** (auto-start on boot), you'll want:

### systemd

Included in Raspberry Pi OS. Allows automatic service startup.

**Manual service installation** (detailed in [Auto-Start with Systemd](../advanced/systemd-service.md)):
```bash
sudo systemctl enable bbl-shutter-cam
sudo systemctl start bbl-shutter-cam
```

### SSH

Included. Allows remote login for configuration & photo review.

**Enable SSH (if not already enabled):**
```bash
sudo raspi-config
# → Interface Options → SSH → Enable
```

### SFTP

Uses built-in SSH. Allows secure file transfer of photos.

**Access from your PC:**
```bash
sftp pi@raspberrypi.local
> cd captures/my-printer
> get *.jpg
```

---

## Pre-flight Checklist

Before starting setup, verify:

- [ ] Raspberry Pi Zero 2 W powered on, SSH-accessible
- [ ] Camera Module 3 NOIR physical installed, recognized
- [ ] CyberBrick powered on, within Bluetooth range
- [ ] Python 3.9+ available
- [ ] Internet connection for dependency installation
- [ ] microSD card has ~5GB free space (for photos)

**All set?** → Continue to [Raspberry Pi Setup](setup-pi.md)
