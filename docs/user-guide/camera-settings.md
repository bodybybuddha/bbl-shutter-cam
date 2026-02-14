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

# Exposure & Color
awb = "daylight"        # White balance
ev = 0                  # Exposure (-10 to +10)
saturation = 1.0        # Color intensity (0.0-2.0)
sharpness = 0.5         # Detail/clarity (0.0-2.0)

# Orientation
rotation = 0            # 0, 90, 180, 270
hflip = false           # Flip horizontally
vflip = false           # Flip vertically

# Noise & Speed
denoise = "hq"          # "off", "fast", "hq"

# Focus (Module 3 specific)
# (Coming in v0.2.0)
```

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

## Focus Tuning (v0.2.0 - Coming Soon)

When `bbl-shutter-cam tune` is available:

```bash
bbl-shutter-cam tune --profile my-printer
```

You'll be able to:
- Lock autofocus or set manual focus distance
- Test near/far/infinity focus
- Save optimal focus for your setup

---

## Next Steps

- [Signal Discovery](../features/signal-discovery.md)
- [Troubleshooting](../troubleshooting.md)
- **Camera calibration (v0.2.0)**: Interactive tuning mode coming soon!
