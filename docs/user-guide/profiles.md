---
layout: page
title: Understanding Profiles & Configuration
nav_order: 5
parent: User Guide
---

# Understanding Profiles & Configuration

## What is a Profile?

A **profile** is a named configuration for a single printer + camera setup. You can have multiple profiles, each with:

- Device information (MAC address, Bluetooth signal mappings)
- Camera settings (resolution, rotation, focus, exposure, etc.)
- Capture behavior (output directory, filename format, etc.)

### Example Use Cases

| Profile Name | Use Case |
|--------------|----------|
| `p1s-office` | Bambu P1S in your office |
| `x1c-garage` | Bambu X1C in your garage |
| `test-bench` | Development/testing setup |

---

## Configuration File Location

```
~/.config/bbl-shutter-cam/config.toml
```

**Full path:**
```bash
/home/pi/.config/bbl-shutter-cam/config.toml
```

**View your config:**
```bash
cat ~/.config/bbl-shutter-cam/config.toml
```

**Edit your config:**
```bash
nano ~/.config/bbl-shutter-cam/config.toml
```

---

## Config File Structure

### Minimal Example (After Setup)

```toml
default_profile = "p1s-office"

[profiles.p1s-office.device]
name = "BBL_SHUTTER"
mac = "B8:F8:62:A9:92:7E"
notify_uuid = "00002a4d-0000-1000-8000-00805f9b34fb"

[profiles.p1s-office.camera]
output_dir = "/home/pi/captures/p1s-office"
filename_format = "%Y%m%d_%H%M%S.jpg"
min_interval_sec = 0.5

[profiles.p1s-office.camera.rpicam]
width = 1920
height = 1080
nopreview = true
```

### Complete Example (With Discovery & Options)

```toml
default_profile = "p1s-office"

[profiles.p1s-office.device]
name = "BBL_SHUTTER"
mac = "B8:F8:62:A9:92:7E"
notify_uuid = "00002a4d-0000-1000-8000-00805f9b34fb"

# Discovered signals (from bbl-shutter-cam debug --update-config)
[[profiles.p1s-office.device.events]]
uuid = "00002a4d-0000-1000-8000-00805f9b34fb"
hex = "4000"
capture = true
name = "manual_button"

[[profiles.p1s-office.device.events]]
uuid = "00002a4d-0000-1000-8000-00805f9b34fb"
hex = "8000"
capture = true
name = "bambu_studio"

[[profiles.p1s-office.device.events]]
uuid = "00002a4d-0000-1000-8000-00805f9b34fb"
hex = "0000"
capture = false
name = "release"

[profiles.p1s-office.camera]
output_dir = "/home/pi/captures/p1s-office"
filename_format = "%Y%m%d_%H%M%S.jpg"
min_interval_sec = 0.5

[profiles.p1s-office.camera.rpicam]
# Resolution
width = 1920
height = 1080

# Preview & Output
nopreview = true

# Orientation
rotation = 0
hflip = false
vflip = false

# Exposure & Color
awb = "daylight"
ev = 0

# Noise & Speed
denoise = "hq"
sharpness = 0.5
```

---

## Section Reference

### [Default Profile]

```toml
default_profile = "p1s-office"
```

Which profile to use when you don't specify `--profile` on the command line.

---

### [profiles.<name>.device]

Device and Bluetooth configuration.

| Key | Type | Auto | Description |
|-----|------|------|-------------|
| `name` | string | Yes* | Device name (e.g., "BBL_SHUTTER") |
| `mac` | string | Yes | MAC address (learned during `setup`) |
| `notify_uuid` | string | Yes | Bluetooth UUID (learned during `setup`) |
| `events` | array | No | Discovered signal mappings (from `debug`) |

**\*Auto**: Set during `bbl-shutter-cam setup`

---

### [profiles.<name>.camera]

Capture behavior and output settings.

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `output_dir` | string | `~/captures/<profile>` | Where to save photos |
| `filename_format` | string | `%Y%m%d_%H%M%S.jpg` | Filename pattern (strftime) |
| `min_interval_sec` | float | 0.5 | Minimum seconds between captures (debounce) |

#### Filename Format

Uses Python `strftime` formatting:

| Code | Example | Meaning |
|------|---------|---------|
| `%Y` | 2026 | 4-digit year |
| `%m` | 02 | 2-digit month |
| `%d` | 14 | 2-digit day |
| `%H` | 15 | 2-digit hour (24-hr) |
| `%M` | 30 | 2-digit minute |
| `%S` | 45 | 2-digit second |

**Examples:**
```toml
filename_format = "%Y%m%d_%H%M%S.jpg"          # 20260214_153045.jpg
filename_format = "%Y-%m-%d %H:%M:%S.jpg"      # 2026-02-14 15:30:45.jpg
filename_format = "capture_%Y%m%d_%H%M%S.jpg" # capture_20260214_153045.jpg
```

---

### [profiles.<name>.camera.rpicam]

Camera hardware settings (passed directly to `rpicam-still`).

#### Resolution

```toml
width = 1920    # Pixels
height = 1080   # Pixels
```

**Common resolutions:**
```toml
width = 1920; height = 1080      # 1080p (HD)
width = 2560; height = 1920      # 1440p
width = 3840; height = 2160      # 2160p (4K) — slower
width = 4656; height = 3496      # Max resolution — very slow
```

**Tip:** Start with 1920×1080. Larger = slower captures, bigger files.

#### Output Control

```toml
nopreview = true    # Don't show preview (headless — always true)
```

#### Orientation

```toml
rotation = 0        # 0, 90, 180, 270
hflip = false       # Flip horizontally
vflip = false       # Flip vertically
```

**Example:** Camera mounted upside-down:
```toml
rotation = 180
hflip = false
vflip = false
```

#### Exposure & Color

```toml
awb = "daylight"    # Auto white balance: "auto", "daylight", "tungsten", "warm", "cool", "shade"
ev = 0              # Exposure compensation: -10 to +10
saturation = 1.0    # Color intensity: 0.0 to 2.0
sharpness = 0.5     # Detail/clarity: 0.0 to 2.0
```

**Examples:**

**Bright enclosure with warm lights:**
```toml
awb = "tungsten"
ev = -2             # Reduce brightness
saturation = 0.8    # Slightly muted
```

**Dark enclosure (NOIR camera):**
```toml
awb = "auto"
ev = 2              # Increase brightness
saturation = 1.0
```

#### Noise & Speed

```toml
denoise = "hq"      # "off", "fast", "hq"
sharpness = 0.5
```

**Note:** HQ denoise is slower but cleaner. Use `fast` for rapid timelapse.

#### Advanced (Optional)

```toml
iso = 100           # Sensor sensitivity (100–800; higher = brighter, noisier)
gain = 1.0          # Sensor gain
shutter = 1000000   # Shutter speed in microseconds
```

---

## Multi-Profile Example

Want to capture from **two printers**?

```toml
default_profile = "p1s-office"

# Printer 1: Bambu P1S in office
[profiles.p1s-office.device]
mac = "B8:F8:62:A9:92:7E"
notify_uuid = "00002a4d-0000-1000-8000-00805f9b34fb"

[profiles.p1s-office.camera]
output_dir = "/home/pi/captures/p1s-office"

[profiles.p1s-office.camera.rpicam]
rotation = 0
width = 1920
height = 1080
awb = "daylight"

# Printer 2: Bambu X1C in garage (different camera angle)
[profiles.x1c-garage.device]
mac = "AA:BB:CC:DD:EE:FF"
notify_uuid = "00002a4d-0000-1000-8000-00805f9b34fb"

[profiles.x1c-garage.camera]
output_dir = "/home/pi/captures/x1c-garage"

[profiles.x1c-garage.camera.rpicam]
rotation = 90       # Different angle
width = 1920
height = 1080
awb = "tungsten"    # Garage lighting
ev = 1              # Brighter
```

**Run each:**
```bash
bbl-shutter-cam run --profile p1s-office
bbl-shutter-cam run --profile x1c-garage
```

---

## Editing the Config File

### Safe Editing

Use a text editor on the Pi:

```bash
nano ~/.config/bbl-shutter-cam/config.toml
```

*(nano: Ctrl+O to save, Ctrl+X to exit)*

Or edit from your PC (via SFTP) and upload back.

### Common Changes

**Change output directory:**
```toml
[profiles.p1s-office.camera]
output_dir = "/data/timelapse"  # ← Update this
```

**Rotate camera (mounted sideways):**
```toml
[profiles.p1s-office.camera.rpicam]
rotation = 90  # ← 0, 90, 180, or 270
```

**Disable Bambu Studio triggers (manual only):**
```toml
[[profiles.p1s-office.device.events]]
hex = "8000"
capture = false  # ← Was true
```

**Change exposure for darker environment:**
```toml
[profiles.p1s-office.camera.rpicam]
ev = 2  # Brighter (was 0)
```

### Verify Changes

After editing, test with dry-run:

```bash
bbl-shutter-cam run --profile p1s-office --dry-run --verbose
```

If no errors, you're good! Then test for real:

```bash
bbl-shutter-cam run --profile p1s-office
```

---

## Troubleshooting Config Issues

**Syntax errors in TOML?**

Tool will show:
```
Error: Failed to parse config file
  Invalid TOML syntax
```

**Solution**: Check for:
- Missing quotes around strings
- Wrong brackets (use `[` for sections, `[[` for arrays)
- Typos in keys

**Profile not found?**

```
KeyError: "Profile 'typo-name' not found in config."
```

**Solution**: Check spelling against `config.toml`. Use auto-complete:
```bash
bbl-shutter-cam run --profile <Tab>  # Shows available profiles
```

---

## Next Steps

- [Camera Settings Deep Dive](camera-settings.md)
- [Signal Discovery](../features/signal-discovery.md)
- [Troubleshooting](../troubleshooting.md)
