---
layout: page
title: Raspberry Pi Setup
nav_order: 3
parent: Installation
---

# Raspberry Pi Setup

Follow this guide to get `bbl-shutter-cam` running on your Raspberry Pi.

## 1. Install Raspberry Pi OS

### Using Raspberry Pi Imager

1. **Download** [Raspberry Pi Imager](https://www.raspberrypi.com/software/) for your PC/Mac
2. **Insert** microSD card into PC
3. **Open** Imager, select:
   - **Device**: Raspberry Pi Zero 2 W (or your model)
   - **OS**: Raspberry Pi OS Lite (Bookworm)
   - **Storage**: Your microSD card
4. **Advanced Options** (gear icon):
   - Set hostname (e.g., `bbl-cam-pi5`)
   - Enable SSH (✓ Use password authentication)
   - Set username/password (e.g., pi / raspberry)
   - Configure WiFi (SSID & password)
5. **Write** to card (takes 1-2 minutes)
6. **Eject** card safely

### Boot and Connect

1. Insert microSD into Pi
2. Connect power (5V USB-C)
3. Wait 30-60 seconds for first boot
4. Connect via SSH:
   ```bash
   ssh pi@bbl-cam-pi5.local
   # Or use IP address if hostname fails:
   ssh pi@192.168.1.XXX
   ```

---

## 2. Verify Camera & Bluetooth

### Check Camera Recognition

```bash
libcamera-hello --list-properties
```

**Expected output** (Camera Module 3 NOIR):
```
Properties of IMX708:
  Location: 0
  Rotation: 0
  ...
```

**Issue?** → See [Camera Not Detected](troubleshoot-setup.md#camera-not-detected)

### Test Camera Capture

```bash
rpicam-still -o test.jpg
ls -lh test.jpg
# -rw-r--r-- 1 pi pi 1234567 Feb 14 15:30 test.jpg
```

If successful, you have a 1.2MB photo. **Delete it:**
```bash
rm test.jpg
```

### Check Bluetooth

```bash
sudo hcitool scan
```

**Expected output** (CyberBrick showing):
```
Scanning ...
        B8:F8:62:A9:92:7E       BBL_SHUTTER
```

If you see `BBL_SHUTTER`, Bluetooth works! ✅

**Issue?** → See [Bluetooth Not Working](troubleshoot-setup.md#bluetooth-not-working) or the detailed [Bluetooth Setup Guide](bluetooth-setup.md) for comprehensive pairing instructions.

---

## 3. Install bbl-shutter-cam

### Clone Repository

```bash
cd ~
git clone https://github.com/bodybybuddha/bbl-shutter-cam.git
cd bbl-shutter-cam
```

### Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
```

You should see `(venv)` prefix in your terminal prompt.

### Install Project

```bash
pip install -e ".[dev]"
```

This installs:
- **Runtime dependencies**: bleak, tomlkit
- **Dev tools**: pytest, black, pylint, mypy (useful if contributing)

**Installation takes 1-2 minutes** (especially mypy).

### Verify Installation

```bash
which bbl-shutter-cam
# /home/pi/bbl-shutter-cam/venv/bin/bbl-shutter-cam

bbl-shutter-cam --version
# (Shows help text if no version yet)

bbl-shutter-cam --help
# Shows all commands: scan, setup, debug, run
```

✅ **You're ready to set up a profile!**

---

## 4. Create Your First Profile

### Scan for Devices

```bash
bbl-shutter-cam scan --name BBL_SHUTTER
```

**Expected output**:
```
[+] Found devices:
  - name='BBL_SHUTTER'  mac=B8:F8:62:A9:92:7E
```

Note the MAC address—you'll need it next.

### Run Setup

```bash
bbl-shutter-cam setup --profile my-printer
```

The tool will:
1. Scan for `BBL_SHUTTER` (by default)
2. Connect to it
3. **Prompt you to press the physical shutter button** on your CyberBrick
4. Learn the Bluetooth signal (takes ~30 seconds)
5. Save configuration to `~/.config/bbl-shutter-cam/config.toml`

**Output:**
```
[+] Setup complete for profile 'my-printer'
    MAC: B8:F8:62:A9:92:7E
    notify_uuid: 00002a4d-0000-1000-8000-00805f9b34fb

[+] Next: dry run
    bbl-shutter-cam run --profile my-printer --dry-run --verbose
[+] Then: run for real
    bbl-shutter-cam run --profile my-printer
```

**Connection issues?** → See the detailed [Bluetooth Setup Guide](bluetooth-setup.md) for step-by-step Bluetooth pairing and troubleshooting.

---

## 5. Test with Dry-Run

Before capturing real photos, test without actually taking photos:

```bash
bbl-shutter-cam run --profile my-printer --dry-run --verbose
```

**Expected behavior**:
1. Connects to CyberBrick via Bluetooth
2. Subscribes to notifications
3. **Press the shutter button** on your CyberBrick
4. Output shows: `SHUTTER PRESS (manual button) 4000`
5. **No photo taken** (dry-run mode)
6. Press Ctrl+C to stop

### Troubleshot If No Response?

See [Run Command Fails](troubleshoot-setup.md#run-command-fails).

---

## 6. Run for Real!

```bash
bbl-shutter-cam run --profile my-printer
```

**How to use:**
1. Press shutter button on CyberBrick
2. Camera captures and saves to: `~/captures/my-printer/YYYYMMDD_HHMMSS.jpg`
3. View the photo:
   ```bash
   ls -lh ~/captures/my-printer/
   ```
4. Press Ctrl+C to stop

---

## 7. Next Steps

### Review Photos

```bash
# View on same system
ls -lh ~/captures/my-printer/*.jpg
file ~/captures/my-printer/*.jpg  # Check file format

# Or download to your PC via SFTP
# (See: Headless Operation guide)
```

### Customize Capture Location

Edit `~/.config/bbl-shutter-cam/config.toml`:

```toml
[profiles.my-printer.camera]
output_dir = "/home/pi/my-prints/timelapse"
filename_format = "%Y%m%d_%H%M%S.jpg"
```

Then create the directory:
```bash
mkdir -p /home/pi/my-prints/timelapse
```

### Discover Unknown Signals (Optional)

If Bambu Studio app sends different signals, discover them:

```bash
bbl-shutter-cam debug --profile my-printer --duration 120 --update-config
```

With your printer running, trigger captures via Bambu Studio app. Signals are saved to config automatically.

→ See [Signal Discovery Guide](../features/signal-discovery.md) for details.

### Enable Auto-Start (Optional)

Want `bbl-shutter-cam` to launch automatically on boot?

→ See [Auto-Start with Systemd](../advanced/systemd-service.md)

### Tune Camera Settings (Upcoming v0.2.0)

Adjust rotation, focus, exposure, white balance:

```bash
bbl-shutter-cam tune --profile my-printer
```

*(Guide available when feature releases)*

---

## Verify Successful Setup

You have a working setup if:

- ✅ `bbl-shutter-cam scan` finds your CyberBrick
- ✅ `setup` completes without errors
- ✅ `--dry-run` shows "SHUTTER PRESS" when you press the button
- ✅ `run` creates photos in `~/captures/my-printer/`

**Next?** → [Understanding Profiles & Configuration](../user-guide/profiles.md)

---

## Troubleshooting

Issues during setup? See the complete [Setup Troubleshooting Guide](troubleshoot-setup.md).
