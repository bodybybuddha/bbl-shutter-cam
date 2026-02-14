---
layout: page
title: Camera Settings & Tuning
nav_order: 6
parent: User Guide
---

# Camera Settings & Tuning

*Detailed guide to rpicam-still options and Raspberry Pi Camera Module 3 tuning.*

## Overview

See [Understanding Profiles & Configuration - Camera Section](profiles.md#profilesnamecaramerarcicam) for the complete reference.

Common settings:

```toml
[profiles.my-printer.camera.rpicam]
# Resolution (1920x1080 recommended for fast timelapse)
width = 1920
height = 1080

# Orientation
rotation = 0            # 0, 90, 180, 270
hflip = false           # Flip horizontally
vflip = false           # Flip vertically

# Focus (Module 3)
autofocus_mode = "auto" # auto, manual, continuous
lens_position = 2.0     # 0.0 (infinity) to ~32 (close); manual mode only

# Exposure & Color
awb = "daylight"        # White balance
ev = 0                  # Exposure (-10 to +10)
saturation = 1.0        # Color intensity (0.0-2.0)
contrast = 1.0          # Contrast (0.0-2.0)
brightness = 0.0        # Brightness (-1.0 to 1.0)
sharpness = 0.5         # Detail/clarity (0.0-2.0)

# Noise & Advanced
denoise = "cdn_hq"      # off, cdn_off, cdn_fast, cdn_hq
metering = "centre"     # centre, spot, matrix, custom
quality = 93            # JPEG quality (0-100)
```

---

## Interactive Tuning (v0.3.0)

**New in v0.3.0:** Use the interactive tuning menu to dial in your settings!

```bash
bbl-shutter-cam tune --profile my-printer
```

The tuning interface lets you:
- 📸 **Take test photos** with current settings
- ⚙️ **Adjust parameters** interactively (no config file editing)
- 💾 **Save settings** directly to your profile
- ↩️ **Rollback** to original settings if needed
- 🔍 **Perfect for SSH/headless** - no GUI required!

### Tuning Workflow

1. **Start tuning:**
   ```bash
   bbl-shutter-cam tune --profile my-printer
   ```

2. **Adjust settings** through the interactive menu:
   - Orientation (rotation, flips)
   - Focus (AF mode, lens position)
   - Exposure & Color (EV, AWB, saturation, etc.)
   - Advanced (denoise, metering, quality, shutter, gain)

3. **Take test photos** (saved to `~/captures/<profile>/tune/`)

4. **View photos** via SFTP/SCP:
   ```bash
   scp pi@pi5.local:~/captures/my-printer/tune/*.jpg .
   ```

5. **Save** when satisfied, or **rollback** to start over

---

## Module 3 Specific Optimizations

### Low Light (NOIR Camera in Dark Enclosures)

```toml
awb = "auto"
ev = 2                  # Increase brightness
saturation = 1.0
iso = 200              # Higher sensitivity
denoise = "hq"         # Reduce noise
```

### Bright Enclosures with Warm Lighting

```toml
awb = "tungsten"       # Adapt to warm lights
ev = -1                # Reduce blown highlights
saturation = 0.9       # Slightly muted
```

---

## Camera Parameter Reference

- [Signal Discovery](../features/signal-discovery.md)
- [Troubleshooting](../troubleshooting.md)
- **Camera calibration (v0.2.0)**: Interactive tuning mode coming soon!
