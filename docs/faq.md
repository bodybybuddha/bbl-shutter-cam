---
layout: page
title: FAQ
nav_order: 8
---

# Frequently Asked Questions

## General

**Q: Can I use a different camera (not Module 3)?**

A: Yes. Module v2 and HQ cameras work, but some settings may differ. Module 3 is recommended for superior autofocus and speed.

**Q: Can I use Wi-Fi instead of Ethernet?**

A: Yes. WiFi works fine for uploads/remote access, though Ethernet is more reliable for headless operation.

**Q: How many photos can I store?**

A: Depends on your SD card. At 1920¹080 JPEG, each photo ~1–2MB. A 64GB card holds ~30,000–60,000 photos.

**Q: What's the maximum capture rate?**

A: ~2–3 photos per second (depending on resolution and camera settings). Typical timelapse uses much slower rates.

---

## Bluetooth & Signals

**Q: What if my CyberBrick sends a different signal?**

A: Use `bbl-shutter-cam debug --profile <name> --duration 60 --update-config` to discover and save it automatically.

**Q: How far can Bluetooth reach?**

A: 10–50 meters line-of-sight. Indoors through concrete/metal: ~10 meters typical. Move the Pi closer if needed.

**Q: Can I use multiple CyberBricks?**

A: Yes, create separate profiles for each:
```toml
[profiles.printer1]
mac = "AA:BB:CC:DD:EE:FF"

[profiles.printer2]
mac = "11:22:33:44:55:66"
```

Run each separately (or with systemd user services).

---

## Camera Settings

**Q: Why are my photos dark?**

A: Increase exposure:
```toml
[profiles.my-printer.camera.rpicam]
ev = 2  # Range: -10 to +10
```

Or improve white balance:
```toml
awb = "tungsten"  # For warm lights
```

**Q: How do I flip/rotate the camera?**

A: Edit config:
```toml
rotation = 90      # 0, 90, 180, 270
hflip = true       # Mirror left-right
vflip = true       # Mirror top-bottom
```

**Q: What's the difference between denoise = "hq" vs "fast"?**

A: **"hq"**: Cleaner, slower (2–3x slower). **"fast"**: Acceptable quality, much faster. Use "fast" for rapid timelapse.

---

## Installation & Troubleshooting

**Q: My setup hangs at "Connecting…"**

A: CyberBrick likely not powered or out of range. Verify:
```bash
sudo hcitool scan | grep BBL_SHUTTER
```

If not found, power on/reposition CyberBrick.

**Q: "Profile not found" error?**

A: Run `bbl-shutter-cam setup --profile my-printer` first.

**Q: rpicam-still not found?**

A: Install it:
```bash
sudo apt update && sudo apt install -y libraspberrypi-bin
```

**Q: Permission denied when saving photos?**

A: Ensure directory exists and is writable:
```bash
mkdir -p ~/captures/my-printer
chmod 755 ~/captures/my-printer
```

---

## Configuration

**Q: Can I run multiple profiles simultaneously?**

A: Yes, with separate processes:
```bash
# Terminal 1
bbl-shutter-cam run --profile printer1

# Terminal 2
bbl-shutter-cam run --profile printer2
```

Or use systemd user services (see [Systemd Auto-Start](advanced/systemd-service.md)).

**Q: How do I backup my config?**

A: Copy the file:
```bash
cp ~/.config/bbl-shutter-cam/config.toml ~/config_backup.toml
```

**Q: Can I manually edit config.toml?**

A: Yes! Use any text editor:
```bash
nano ~/.config/bbl-shutter-cam/config.toml
```

Then test with `--dry-run` before running for real.

---

## Data & Storage

**Q: How do I download photos from my Pi?**

A: Use SFTP:
```bash
# From your PC:
sftp pi@raspberrypi.local
> cd captures/my-printer
> get *.jpg
```

Or SCP:
```bash
scp -r pi@raspberrypi.local:captures/my-printer ./local-folder
```

**Q: Can I automatically upload to cloud?**

A: Not yet (future feature). For now, manually download or set up a cron job with rsync/rclone.

**Q: How do I delete old photos?**

A: SSH to Pi:
```bash
# Remove oldest photos (keep newest 500)
ls -t ~/captures/my-printer/*.jpg | tail -n +501 | xargs rm
```

---

## Performance

**Q: Why are captures slower than expected?**

A: Factors that slow capture:
- **Resolution**: Higher = slower. Use 1920×1080 for fast timelapse.
- **Denoise**: "hq" is 2–3× slower than "fast".
- **Autofocus**: Manual focus (lens_position) faster than auto.
- **Camera**: Module 3 faster than v2.

**Optimize:**
```toml
width = 1920
height = 1080
denoise = "fast"      # Not "hq"
autofocus = "manual"  # Lock focus value
```

**Q: Can I capture "burst" mode (multiple per second)?**

A: Set a tight `min_interval_sec`:
```toml
min_interval_sec = 0.1  # 100ms = 10 captures/sec (hardware dependent)
```

Be aware: May overwhelm the camera/Pi. Test with `--dry-run` first.

---

## Advanced / Development

**Q: How do I extend the app with custom triggers?**

A: See [Extending & Contributing](advanced/extending.md).

**Q: Can I use a different camera library (not rpicam)?**

A: Not yet, but the architecture supports it. See [Extending & Contributing](advanced/extending.md).

**Q: How do I debug issues?**

A: Use verbose logging:
```bash
bbl-shutter-cam run --profile my-printer --verbose --log-level debug --log-file ~/app.log
```

Then review:
```bash
tail -f ~/app.log
```

---

## Not Found Here?

- **Setup issues?** → [Setup Troubleshooting](installation/troubleshoot-setup.md)
- **General problems?** → [Troubleshooting Guide](troubleshooting.md)
- **Found a bug?** → [GitHub Issues](https://github.com/bodybybuddha/bbl-shutter-cam/issues)
