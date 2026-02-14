---
layout: page
title: Dynamic Signal Discovery (Stage 2.5)
nav_order: 4
parent: Features
---

# Dynamic Signal Discovery & Event Configuration

## What is Signal Discovery?

`bbl-shutter-cam` listens for Bluetooth signals from your CyberBrick. **Signal Discovery** lets you:

1. **Capture all Bluetooth traffic** sent by your device
2. **Identify unknown signals** (not just the hardcoded ones)
3. **Automatically update your config** with discovered signals
4. **Control which signals trigger photos**

### Why This Matters

Different devices and software send different signals:
- **Manual shutter button**: `0x4000` (hardware button press)
- **Bambu Studio app**: `0x8000` (software trigger)
- **Unknown devices**: Could be `0xXXXX` (your custom hardware?)

Without discovery, you'd miss signals and captures wouldn't work. Discovery solves this automatically.

---

## The Debug Command

### Basic Usage

Listen for all Bluetooth signals for 60 seconds:

```bash
bbl-shutter-cam debug --profile my-printer --duration 60
```

**Output while you press the shutter:**

```
[15:42:03.456] 00002a4d-0000-1000-8000-00805f9b34fb
           HEX: 4000
           DEC:  64   0
           LEN: 2 bytes

[15:42:03.500] 00002a4d-0000-1000-8000-00805f9b34fb
           HEX: 0000
           DEC:   0   0
           LEN: 2 bytes

[15:42:45.789] 00002a4d-0000-1000-8000-00805f9b34fb
           HEX: 8000
           DEC: 128   0
           LEN: 2 bytes
```

**After 60 seconds, you get a summary:**

```
============================================================
SIGNAL SUMMARY
============================================================

00002a4d-0000-1000-8000-00805f9b34fb:
  4000                 (received 3 time(s))
  0000                 (received 3 time(s))
  8000                 (received 3 time(s))
```

### Command Options

```bash
bbl-shutter-cam debug --help
```

| Option | Default | Description |
|--------|---------|-------------|
| `--profile` | Required | Profile name (e.g., `my-printer`) |
| `--mac` | (none) | Override device MAC (pull from profile if not set) |
| `--duration` | 120 | Listen for N seconds (0 = infinite) |
| `--update-config` | False | Auto-save discovered signals to config |

---

## Workflow: Discovering Signals

### Scenario 1: Manual Button Press Only

You want to capture on manual shutter button presses.

**Step 1: Start discovery**
```bash
bbl-shutter-cam debug --profile p1s-office --duration 30
```

**Step 2: Press the shutter button 3–5 times**

You'll see output like:
```
[15:30:01.234] 00002a4d...
           HEX: 4000
           DEC:  64   0
           LEN: 2 bytes
```

**Step 3: Let it finish, review summary**

You'll see `4000` (press) and `0000` (release) signals.

**Done!** The defaults handle this already (0x4000 captures, 0x0000 doesn't).

---

### Scenario 2: Bambu Studio App Integration

You want **both** manual button AND app triggers to work.

**Step 1: Start discovery**
```bash
bbl-shutter-cam debug --profile p1s-office --duration 120 --update-config
```

**Step 2: Trigger captures both ways:**
- Manually press the shutter button 2–3 times
- Trigger captures via Bambu Studio app 2–3 times (if available)

**Output shows:**
```
[15:32:01.111] 00002a4d...
           HEX: 4000
           LEC:  64   0
           LEN: 2 bytes

[15:32:45.678] 00002a4d...
           HEX: 8000
           DEC: 128   0
           LEN: 2 bytes

[15:32:46.234] 00002a4d...
           HEX: 0000
           DEC:   0   0
           LEN: 2 bytes
```

**Step 3: With `--update-config`, signals are automatically saved:**

```
✓ Config updated with 3 signal(s)
  Location: /home/pi/.config/bbl-shutter-cam/config.toml
```

**Done!** Your config now includes both 0x4000 and 0x8000 as capture triggers.

---

### Scenario 3: Custom / Unknown Hardware

You have a custom device sending unfamiliar signals.

**Step 1: Start discovery in infinite mode**
```bash
bbl-shutter-cam debug --profile my-printer --duration 0 --update-config
```

*(Ctrl+C to stop)*

**Step 2: Trigger your custom device repeatedly**

Unknown signals appear:
```
[15:35:10.456] 00002a4d...
           HEX: FF00
           DEC: 255   0
           LEN: 2 bytes
```

**Step 3: Stop with Ctrl+C**

```
============================================================
SIGNAL SUMMARY
============================================================

00002a4d-0000-1000-8000-00805f9b34fb:
  4000                 (received 5 time(s))
  8000                 (received 3 time(s))
  FF00                 (received 2 time(s))
  0000                 (received 10 time(s))
```

**Step 4: Check config**

```bash
cat ~/.config/bbl-shutter-cam/config.toml
```

The `--update-config` flag saved all signals. Now edit to **enable/disable** triggers:

```toml
[[profiles.my-printer.device.events]]
uuid = "00002a4d-0000-1000-8000-00805f9b34fb"
hex = "FF00"
capture = true          # ← Change to false if you don't want photos on this signal
name = "custom_device"  # ← Optional label
```

---

## Understanding Signals

### Signal Anatomy

Each signal has:

| Field | Example | Meaning |
|-------|---------|---------|
| **UUID** | `00002a4d...` | Bluetooth characteristic ID (where signal comes from) |
| **HEX** | `4000` | Signal bytes in hexadecimal |
| **DEC** | 64, 0 | Same bytes in decimal (often clearer for debugging) |
| **LEN** | 2 | Number of bytes |

### Common Signals

#### 0x4000 (Manual Button)
- **Meaning**: CyberBrick physical button pressed
- **Frequency**: Once per press
- **Followed by**: 0x0000 (release)
- **Capture**: YES (by default)

#### 0x8000 (Bambu Studio)
- **Meaning**: Bambu Studio app sent trigger signal
- **Frequency**: Once per app press
- **Followed by**: 0x0000 (release)
- **Capture**: YES (by default)

#### 0x0000 (Release)
- **Meaning**: Button/signal released
- **Frequency**: Every time after a press
- **Capture**: NO (by default—don't waste space on nothing)

---

## Configuration File Format

After discovery, your config looks like:

```toml
[profiles.p1s-office.device]
mac = "B8:F8:62:A9:92:7E"
notify_uuid = "00002a4d-0000-1000-8000-00805f9b34fb"

# Signal events (auto-discovered)
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
```

### Modifying Events

You can **manually edit** this TOML to control behavior:

**Disable Bambu Studio triggers:**
```toml
[[profiles.p1s-office.device.events]]
hex = "8000"
capture = false    # ← Changed from true
```

**Add custom signal:**
```toml
[[profiles.p1s-office.device.events]]
uuid = "00002a4d-0000-1000-8000-00805f9b34fb"
hex = "C000"       # Your custom signal
capture = true
name = "my_hardware"
```

**Re-run discovery without overwriting:**

```bash
# Discovers new signals without losing manual edits
bbl-shutter-cam debug --profile p1s-office --duration 60
# (Don't use --update-config; review manually instead)
```

---

## Advanced: Multiple UUIDs

If signals come from **different Bluetooth characteristics** (different UUIDs):

```
[15:40:01.234] 00002a4d-0000-1000-8000-00805f9b34fb
           HEX: 4000

[15:40:10.456] 93db79cc-15d5-44fa-ab79-70092a3348c5    ← Different UUID!
           HEX: F001
```

Both can be configured:

```toml
[[profiles.my-printer.device.events]]
uuid = "00002a4d-0000-1000-8000-00805f9b34fb"
hex = "4000"
capture = true

[[profiles.my-printer.device.events]]
uuid = "93db79cc-15d5-44fa-ab79-70092a3348c5"    # ← Different UUID
hex = "F001"
capture = true
```

The app listens on **all configured UUIDs**.

---

## Tips & Best Practices

### 1. Test Thoroughly

Always run `--dry-run` first:
```bash
bbl-shutter-cam run --profile p1s-office --dry-run --verbose
```

Verify signals show before enabling real capture.

### 2. Use `--update-config` Carefully

`--update-config` **overwrites** the events section:

```bash
# Safe: Just view signals (manual review)
bbl-shutter-cam debug --profile p1s-office --duration 60

# Careful: Auto-overwrites; review changes after
bbl-shutter-cam debug --profile p1s-office --duration 60 --update-config
```

**Best practice**: Run *without* `--update-config` first, review output, then decide if you want to update.

### 3. Test Before Long Prints

Run in `--dry-run` mode during a real print to ensure both manual and app triggers work:

```bash
# Terminal 1: Dry-run mode
bbl-shutter-cam run --profile p1s-office --dry-run --verbose

# Terminal 2: Trigger captures while printer runs
# Press shutter button, use app, etc.
# Watch Terminal 1 for "SHUTTER PRESS" messages
```

### 4. Monitor First Long Run

When you finally run for real:
```bash
# Terminal 1
bbl-shutter-cam run --profile p1s-office --verbose

# Terminal 2 (on same Pi or different machine)
tail -f ~/.config/bbl-shutter-cam/app.log
# OR (if you can watch the Pi)
ls ~/captures/p1s-office/*.jpg
# Refreshes as photos are captured
```

---

## Troubleshooting Signal Discovery

### No Signals Appear

**Problem**: `debug` command runs but no output appears.

**Causes**:
- CyberBrick not powered on
- CyberBrick out of Bluetooth range
- Notifications not subscribed to

**Solutions**:
1. Verify CyberBrick is on and nearby
2. Check Bluetooth scope: `sudo hcitool scan`
3. Try with shorter `--duration`: `--duration 10`
4. Check logs: Add `--log-level debug` flag

```bash
bbl-shutter-cam debug --profile p1s-office --duration 30 --log-level debug
```

### Too Many Signals / Noise

**Problem**: Hundreds of signals from other sources.

**Causes**:
- Multiple BLE devices nearby
- System in noisy environment

**Solutions**:
- Run away from other BLE devices (move the Pi outdoors temporarily)
- Reduce duration: `--duration 30`
- Press/trigger *slowly* (big gaps between actions) to spot your signals

### Signals Lost After Config Update

**Problem**: You ran `--update-config` and lost your manual edits.

**Solution**: git/version control! If tracking in git:
```bash
git diff ~/.config/bbl-shutter-cam/config.toml
git checkout ~/.config/bbl-shutter-cam/config.toml  # Restore
```

Otherwise, re-edit manually or re-run discovery.

---

## Next Steps

- **Ready to run?** → [Quick Start Guide](../user-guide/quick-start.md)
- **Need to tune camera?** → [Camera Settings](../user-guide/camera-settings.md) (v0.2.0+)
- **More help?** → [Troubleshooting](../troubleshooting.md) or [FAQ](../faq.md)
