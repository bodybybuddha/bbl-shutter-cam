---
layout: page
title: Quick Start
nav_order: 1
parent: User Guide
---

# Quick Start Guide

Get `bbl-shutter-cam` running in **5 minutes**.

## Prerequisites

- ✅ Raspberry Pi (Zero 2 W recommended)
- ✅ Camera Module 3 NOIR
- ✅ Bambu Lab CyberBrick (BBL_SHUTTER)
- ✅ Raspberry Pi OS Lite installed
- ✅ SSH access to your Pi

**Detailed requirements?** → [Hardware & Software Requirements](../installation/requirements.md)

---

## Step 1: Install

SSH into your Pi and choose one of the install methods below.

### Option A: Standalone binary (recommended)

1. Download the latest release from GitHub.
2. Choose the correct Pi architecture:
    - `bbl-shutter-cam-<version>-linux-arm64` (64-bit)
    - `bbl-shutter-cam-<version>-linux-armv7` (32-bit)
3. Make it executable:

```bash
chmod +x bbl-shutter-cam-<version>-linux-arm64
./bbl-shutter-cam-<version>-linux-arm64 --help
```

### Option B: From source

```bash
cd ~
git clone https://github.com/bodybybuddha/bbl-shutter-cam.git
cd bbl-shutter-cam

python3 -m venv venv
source venv/bin/activate
pip install -e "."
```

**Time:** ~2 minutes

---

## Step 2: Test Camera & Bluetooth

```bash
# Test camera
rpicam-still -o test.jpg && rm test.jpg && echo "✅ Camera OK"

# Test Bluetooth
# If the shutter is already paired, it may not appear in scans while sleeping.
bluetoothctl devices | grep BBL_SHUTTER && echo "✅ Bluetooth paired"
# If not paired yet, scan and press the shutter to wake it.
# bluetoothctl
# scan on
```

Both should work!

---

## Step 3: Create Profile

```bash
bbl-shutter-cam setup --profile my-printer
```

**When prompted**: Press the physical shutter button on your CyberBrick.

**Output should show:**
```
✓ Setup complete for profile 'my-printer'
    MAC: B8:F8:62:A9:92:7E
    notify_uuid: 00002a4d-0000-1000-8000-00805f9b34fb
```

---

## Step 4: Test with Dry-Run

```bash
bbl-shutter-cam run --profile my-printer --dry-run --verbose
```

**Press the shutter button.** You should see:
```
SHUTTER PRESS (manual button) 4000
```

**No photo taken** (it's a dry-run).

Press Ctrl+C to stop.

---

## Step 5: Run for Real!

```bash
bbl-shutter-cam run --profile my-printer
```

**Press shutter. Photo saves to:**
```
~/captures/my-printer/20260214_153045.jpg
```

**Check it:**
```bash
ls ~/captures/my-printer/*.jpg
```

---

## Done! 🎉

You now have working time-lapse capture!

### Next Steps

- **Multiple printers?** → [Profiles & Configuration](profiles.md)
- **Rotate/flip camera?** → [Camera Settings](camera-settings.md)
- **Bambu Studio app triggers?** → [Signal Discovery](../features/signal-discovery.md)
- **Auto-start on boot?** → [Systemd Auto-Start](../advanced/systemd-service.md)
- **Issues?** → [Troubleshooting](../troubleshooting.md)

### Common Commands

```bash
# List available profiles
cat ~/.config/bbl-shutter-cam/config.toml

# Change default profile
# (Edit config.toml, change default_profile = "my-printer")

# Run with verbose output
bbl-shutter-cam run --profile my-printer --verbose

# Discover unknown signals
bbl-shutter-cam debug --profile my-printer --duration 60 --update-config

# Dry-run before real captures
bbl-shutter-cam run --profile my-printer --dry-run
```
