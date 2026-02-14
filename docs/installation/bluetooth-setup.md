---
layout: page
title: Bluetooth Setup on Raspberry Pi
nav_order: 2
parent: Installation & Setup
---

# Bluetooth Setup on Raspberry Pi

Complete step-by-step guide to pair your Bambu Lab CyberBrick Time-Lapse Kit (BBL_SHUTTER) with a Raspberry Pi using Bluetooth.

## Prerequisites

- Raspberry Pi with Bluetooth capability (Pi Zero 2 W, Pi 4, or Pi 5)
- Bambu Lab CyberBrick Time-Lapse Kit (BBL_SHUTTER)
- SSH access to your Pi or direct terminal access
- Administrator/sudo privileges

---

## Step 1: Verify Bluetooth is Not Blocked

First, check the Bluetooth radio status using `rfkill`:

```bash
rfkill
```

Expected output:

```
ID  TYPE      DEVICE      SOFT      HARD
0   bluetooth hci0        unblocked unblocked
1   wlan      wlan0       unblocked unblocked
```

If Bluetooth shows as blocked, unblock it:

```bash
sudo rfkill unblock bluetooth
```

---

## Step 2: Power Up the Bluetooth Adapter

Start the Bluetooth control utility:

```bash
bluetoothctl
```

You should see a prompt like:

```
[bluetooth]#
```

Check if Bluetooth is powered on:

```
[bluetooth]# show
```

Expected output (abbreviated):

```
Controller AA:BB:CC:DD:EE:FF (public)
	Name: 'raspberrypi'
	Alias: 'raspberrypi'
	Class: 0x0c010c
	Powered: yes
	Discoverable: no
	...
```

If `Powered: no`, power it on:

```bash
power on
```

Then verify:

```bash
show
```

You should now see `Powered: yes`.

---

## Step 3: Enable Bluetooth Agent

Set up the agent for pairing:

```bash
agent on
default-agent
```

Example output:

```
[bluetooth]# agent on
Agent registered
[bluetooth]# default-agent
Default agent request successful
[bluetooth]#
```

---

## Step 4: Scan for Your CyberBrick

**On the CyberBrick:**
1. Press and **hold** the multifunction button for 3-5 seconds
2. Device should enter pairing mode (look for LED indicator)

**On the Raspberry Pi:**
Start scanning:

```bash
scan on
```

Wait for the BBL_SHUTTER to appear (may take 5-10 seconds):

```
Discovery started
[NEW] Device AA:BB:CC:DD:EE:FF BBL_SHUTTER
[bluetooth]#
```

Note the MAC address (e.g., `AA:BB:CC:DD:EE:FF`).

---

## Step 5: Pair the Device

Stop scanning first:

```bash
scan off
```

Then pair using the MAC address you noted:

```bash
pair AA:BB:CC:DD:EE:FF
```

Expected output:

```
Attempting to pair with AA:BB:CC:DD:EE:FF
[CHG] Device AA:BB:CC:DD:EE:FF Connected: yes
[CHG] Device AA:BB:CC:DD:EE:FF UUIDs: 180a0000-0000-1000-8000-00805f9b34fb
[CHG] Device AA:BB:CC:DD:EE:FF Paired: yes
Pairing successful
[CHG] Device AA:BB:CC:DD:EE:FF Connected: no
[BAT] Device AA:BB:CC:DD:EE:FF Battery: 85%
[bluetooth]#
```

---

## Step 6: Trust the Device

While still in bluetoothctl, trust the device so it auto-connects:

```bash
trust AA:BB:CC:DD:EE:FF
```

Expected output:

```
[CHG] Device AA:BB:CC:DD:EE:FF Trusted: yes
Changing AA:BB:CC:DD:EE:FF trust succeeded
[bluetooth]#
```

Verify with `info`:

```bash
info AA:BB:CC:DD:EE:FF
```

Look for `Trusted: yes` in the output:

```
Device AA:BB:CC:DD:EE:FF (public)
	Name: BBL_SHUTTER
	...
	Paired: yes
	Trusted: yes
	Connected: no
	...
```

---

## Step 7: Check All Devices

List all paired devices:

```bash
devices
```

Example output:

```
Device AA:BB:CC:DD:EE:FF BBL_SHUTTER
[bluetooth]#
```

Exit bluetoothctl:

```bash
quit
```

---

## Verification

Your CyberBrick is now paired and ready! To verify from the command line:

```bash
sudo bluetoothctl info AA:BB:CC:DD:EE:FF
```

You should see `Paired: yes` and `Trusted: yes`.

---

## Troubleshooting

### Device Not Found During Scan

- Ensure CyberBrick is in pairing mode (multifunction button held for 3+ seconds)
- Check Bluetooth isn't blocked: `rfkill`
- Try increasing scan timeout: wait 15+ seconds before giving up
- Try scanning again in fresh bluetoothctl session

### Pairing Fails

- Device may have already paired with another device (reset if possible)
- Try unpairing first:
  ```bash
  remove AA:BB:CC:DD:EE:FF
  ```
- Then repeat pairing steps

### Device Shows as Connected but No Signal Received

- Device is in sleep mode; press the shutter button to wake it
- Check signal is reaching the Pi with debugging:
  ```bash
  bbl-shutter-cam debug --profile your-profile --mac AA:BB:CC:DD:EE:FF
  ```

### Bluetooth Keeps Disconnecting

- Check battery level: `bluetoothctl show`
- Increase `reconnect_delay` in configuration if needed (default: 2 seconds)
- Ensure Pi Bluetooth antenna is properly seated

---

## Next Steps

Once Bluetooth is configured, you're ready to:

1. [Configure your first profile](quick-start.md)
2. Learn about [trigger signals](signal-discovery.md)
3. Set up [camera settings](../user-guide/camera-settings.md)

See [Quick Start Guide](quick-start.md) for the next steps in setting up bbl-shutter-cam.
