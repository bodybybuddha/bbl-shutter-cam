---
layout: page
title: Troubleshooting Setup
nav_order: 4
parent: Installation
---

# Setup Troubleshooting

Having issues during installation? Find your problem below.

## Camera Not Detected

### Symptom
```bash
libcamera-hello --list-properties
# (no output, or error about IMX708)
```

### Causes
- Camera not physically connected
- Camera ribbon cable loose
- Camera not enabled in raspi-config
- Wrong camera model

### Solutions

**1. Check physical connection:**
- Power off Pi
- Gently disconnnect/reconnect camera ribbon (slot next to USB)
- Power back on

**2. Enable camera in software:**
```bash
sudo raspi-config
# → Interface Options → Legacy Camera → Enable (if available)
# OR check if "Camera" is already enabled under Interface Options

# Then reboot:
sudo reboot
```

**3. Verify camera type:**
```bash
vcgencmd get_camera
# Output: supported=1 detected=1 ✓ Good
```

**4. Update firmware:**
```bash
sudo rpi-update
sudo reboot
```

---

## Bluetooth Not Working

### Symptom
```bash
sudo hcitool scan
# "hci0: command not understood"
# Or: No devices found
```

### Causes
- Bluetooth hardware not recognized
- Services not running
- Range/interference issues
- CyberBrick not powered on

### Solutions

**1. Check Bluetooth status:**
```bash
sudo systemctl status bluetooth
# Should show "active (running)"

# If not:
sudo systemctl start bluetooth
sudo systemctl enable bluetooth
```

**2. Check HCI device:**
```bash
hciconfig
# Should show: hci0: ... UP RUNNING

# If DOWN:
sudo hciconfig hci0 up
```

**3. Verify CyberBrick:**
- Power cycle the CyberBrick
- Move Pi within 5 meters
- Try scan again: `sudo hcitool scan`

**4. Last resort — firmware update:**
```bash
sudo apt update && sudo apt upgrade -y
sudo reboot
```

---

## Run Command Fails

### Symptom
```bash
bbl-shutter-cam run --profile my-printer
# Error: "Profile not found"
```

### Causes
- Typo in profile name
- Profile not created (setup not run)
- Config file missing

### Solutions

**1. List available profiles:**
```bash
cat ~/.config/bbl-shutter-cam/config.toml
# Look for [profiles.XXX] sections
```

**2. Check exact profile name:**
```bash
bbl-shutter-cam run --profile my-printer
# ↑ Match exactly to config file
```

**3. Recreate if missing:**
```bash
bbl-shutter-cam setup --profile my-printer
```

---

### Symptom
```bash
bbl-shutter-cam run --profile my-printer
# Error: "[!] Profile has no MAC. Run setup first."
```

### Causes
- Setup not completed
- Setup failed silently
- Config file corrupted

### Solutions

**1. Run setup again:**
```bash
bbl-shutter-cam setup --profile my-printer
```

**2. Test with dry-run:**
```bash
bbl-shutter-cam run --profile my-printer --dry-run --verbose
```

---

### Symptom
```bash
bbl-shutter-cam run --profile my-printer --dry-run --verbose
# "Connecting…" but hangs forever
```

### Causes
- CyberBrick not powered on
- Bluetooth connection issues
- Wrong MAC address

### Solutions

**1. Verify CyberBrick:**
- Is it powered on?
- Does `sudo hcitool scan` find it?

**2. Test connection directly:**
```bash
python3 -c "
from bleak import BleakScanner
import asyncio

async def test():
    devices = await BleakScanner.discover()
    for d in devices:
        if 'SHUTTER' in (d.name or ''):
            print(f'Found: {d.name} at {d.address}')

asyncio.run(test())
"
```

**3. Force reconnect:**
Press a button on the CyberBrick, then immediately run:
```bash
bbl-shutter-cam run --profile my-printer --dry-run --verbose
```

---

## Photo Capture Not Working

### Symptom
```bash
bbl-shutter-cam run --profile my-printer --dry-run --verbose
# Shows "SHUTTER PRESS" but no photo saved
```

### Causes
- Output directory doesn't exist
- Permission issues
- rpicam-still not installed

### Solutions

**1. Create output directory:**
```bash
mkdir -p ~/captures/my-printer
chmod 755 ~/captures/my-printer
```

**2. Verify rpicam-still:**
```bash
which rpicam-still
# /usr/bin/rpicam-still

# Test it:
rpicam-still -o test.jpg
ls test.jpg  # Should exist
rm test.jpg
```

**3. Check config output path:**
```bash
grep output_dir ~/.config/bbl-shutter-cam/config.toml
# Make sure it exists:
ls -ld /path/from/config
```

---

## Config File Issues

### Symptom
```
Error parsing config file: Invalid TOML
```

### Causes
- Syntax error in TOML
- Missing quotes/brackets
- Typo in section names

### Solutions

**Validate TOML:**
```bash
python3 -c "
from tomlkit import parse
with open('~/.config/bbl-shutter-cam/config.toml') as f:
    parse(f.read())
print('✓ Valid TOML')
" 2>&1
```

**Check for common errors:**
- Missing quotes: `name = value` should be `name = "value"`
- Wrong brackets: `[section]` vs `[[array]]`
- Indentation: TOML doesn't require indentation

---

## More Help

- [FAQ](../faq.md)
- [General Troubleshooting](../troubleshooting.md)
- [GitHub Issues](https://github.com/bodybybuddha/bbl-shutter-cam/issues)
