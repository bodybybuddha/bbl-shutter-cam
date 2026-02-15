---
layout: page
title: General Troubleshooting
nav_order: 7
---

# Troubleshooting

Issues? Find your problem below or in our [FAQ](faq.md).

## Common Issues

### Setup/Installation Issues

→ See [Setup Troubleshooting](installation/troubleshoot-setup.md)

- Camera not detected
- Bluetooth not working
- Pi can't connect to networks

### Run Command Issues

**"Profile not found"**
```bash
bbl-shutter-cam run --profile typo-name
# Error: Profile 'typo-name' not found in config.
```

**Solution**: Check exact profile name in config:
```bash
cat ~/.config/bbl-shutter-cam/config.toml
```

**Hanging at "Connecting…"**

Likely CyberBrick is asleep, off, or out of range. Try:
```bash
bluetoothctl devices | grep BBL_SHUTTER
```
If it is paired but not found in scans, press the shutter button to wake it and
retry `setup` or `run --dry-run`.

**Rapid connect/disconnect loop**

If `bluetoothctl` shows the device repeatedly connecting and disconnecting, the pairing may be corrupted. Remove and re-pair:

```bash
bluetoothctl
remove B8:F8:62:A9:92:7E  # Use your device's MAC
scan on
# Press the shutter button multiple times
pair B8:F8:62:A9:92:7E
trust B8:F8:62:A9:92:7E
exit
```

Then retry `setup` or `run --dry-run`.

### Photo Capture Issues

**Photos not appearing**

Check:
1. Output directory exists: `ls ~/captures/my-printer/`
2. rpicam-still works: `rpicam-still -o test.jpg`
3. Config output path is correct

**Photos are dark/too bright**

Adjust exposure in config:
```toml
[profiles.my-printer.camera.rpicam]
ev = 2  # Brighter (range: -10 to +10)
```

Then test: `bbl-shutter-cam run --profile my-printer --dry-run`

---

## Getting Help

1. **Check [FAQ](faq.md)** for common questions
2. **Review [Setup Troubleshooting](installation/troubleshoot-setup.md)** for installation issues
3. **Enable verbose logging:**
   ```bash
   bbl-shutter-cam run --profile my-printer --verbose --log-level debug
   ```
4. **Submit issue on [GitHub](https://github.com/bodybybuddha/bbl-shutter-cam/issues)** with:
   - Error message (full output)
   - Your hardware (Pi model, camera, OS version)
   - Steps to reproduce
   - Config file (redact MAC if desired)

---

## Debug Mode

For deep troubleshooting:

```bash
bbl-shutter-cam run --profile my-printer \
  --verbose \
  --log-level debug \
  --log-file ~/debug.log
```

Review logs:
```bash
tail -f ~/debug.log
```

---

## Logging

Enable to file for review later:

```bash
# Append to log file
bbl-shutter-cam run --profile my-printer --log-file ~/bbl.log

# Review
cat ~/bbl.log
tail -20 ~/bbl.log
```

---

## System Resources

Check Pi resources while running:

```bash
# Monitor CPU/memory
top

# Disk space
df -h
du -sh ~/captures/

# Network (if using remote access)
ifconfig
```

---

## Signal Discovery Issues

→ See [Signal Discovery Troubleshooting](features/signal-discovery.md#troubleshooting-signal-discovery)

Issues with the `bbl-shutter-cam debug` command.

---

## More Help

- [Quick Start](user-guide/quick-start.md)
- [Setup Troubleshooting](installation/troubleshoot-setup.md)
- [FAQ](faq.md)
- [GitHub Issues](https://github.com/bodybybuddha/bbl-shutter-cam/issues)
