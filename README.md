# bbl-shutter-cam

Use a **Bambu Lab CyberBrick / BBL_SHUTTER Bluetooth shutter** to trigger photos on a **Raspberry Pi (Zero 2 W recommended)** using `rpicam-still`.

This project is designed for **headless, reliable time‑lapse capture** inside 3D‑printer enclosures and similar setups.

---

## What this does

* Pairs a Raspberry Pi with the **BBL_SHUTTER** (CyberBrick Time‑Lapse Kit)
* Listens for the shutter press BLE notification
* Triggers `rpicam-still` on each press
* Supports multiple printer/camera profiles via TOML
* Runs headless with optional log files

---

## Requirements

### Hardware

* Raspberry Pi Zero 2 W (recommended)
* Raspberry Pi camera (v2 / HQ / compatible libcamera device)
* Bambu Lab CyberBrick Time‑Lapse Kit (BBL_SHUTTER)

### Software

* Raspberry Pi OS Lite (Bookworm recommended)
* Python 3.9+
* `libcamera-apps` (for `rpicam-still`)
* Bluetooth enabled (`bluez`)

---

## Install system dependencies

```bash
sudo apt update
sudo apt install -y \
  python3 \
  python3-venv \
  python3-pip \
  bluetooth \
  bluez \
  libcamera-apps
```

Enable Bluetooth:

```bash
sudo systemctl enable bluetooth
sudo systemctl start bluetooth
```

---

## Pairing the BBL_SHUTTER

Some tips on the use of **bluetoothctl** can be found here: [raspberry-pi-bluetooth-setup](https://raspberrytips.com/raspberry-pi-bluetooth-setup/)

The below is just some notes on how to get it to work.  Need to update it a bit more with some details.  For instance, need to make sure bluetooth isn't blocked.  In addition, once a the time-lapse kit is paired, need to trust the device.  

Put the CyberBrick Time‑Lapse Kit into pairing mode, then:

```bash
bluetoothctl
```

Inside the prompt:

```text
power on
agent on
default-agent
scan on
```

When you see `BBL_SHUTTER`, note the MAC address, then:

```text
pair XX:XX:XX:XX:XX:XX
trust XX:XX:XX:XX:XX:XX
connect XX:XX:XX:XX:XX:XX
exit
```

> Pairing only needs to be done **once**. The device will reconnect automatically when awake.

---

## Install bbl-shutter-cam (Developer Install)

From the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -e .
```

Verify:

```bash
bbl-shutter-cam --help
```

---

## Configuration

An example configuration is provided:

```text
examples/config.example.toml
```

Copy it to:

```bash
mkdir -p ~/.config/bbl-shutter-cam
cp examples/config.example.toml ~/.config/bbl-shutter-cam/config.toml
```

Edit the file to match your camera orientation, lighting, and output directory.

Multiple printer/camera setups can be defined as **profiles**.

---

## Initial setup (learn the shutter UUID)

Run setup once per profile:

```bash
bbl-shutter-cam setup --profile p1s-office
```

You will be prompted to **press the shutter button**. The tool will learn which BLE notify UUID corresponds to the press event and store it in the config.

---

## Run (dry‑run first)

Dry run (no photos taken):

```bash
bbl-shutter-cam run --profile p1s-office --dry-run --verbose
```

You should see log output when the shutter is pressed.

---

## Run for real

```bash
bbl-shutter-cam run --profile p1s-office
```

Photos will be saved to the configured output directory.

---

## Logging & Troubleshooting

### Log level

```bash
bbl-shutter-cam --log-level debug run --profile p1s-office
```

Levels:

* `debug` – BLE retries, notify subscriptions, camera commands
* `info` – normal operation (default)
* `warning` – warnings only
* `error` – errors only

---

### Log format

Enable timestamps:

```bash
bbl-shutter-cam --log-format time run --profile p1s-office
```

---

### Log file (recommended for headless use)

```bash
bbl-shutter-cam \
  --log-level debug \
  --log-format time \
  --log-file ~/.log/bbl-shutter-cam.log \
  run --profile p1s-office --verbose
```

Log directories are created automatically.

---

## Notes & tips

* BLE devices may only connect when awake — press the shutter if reconnects stall
* Use fixed shutter/gain settings to avoid enclosure flicker
* `min_interval_sec` prevents accidental double‑triggers

---

## License

MIT

---

## Status

This project is **actively developed** and designed to be extended with:

* Camera presets
* systemd service support
* Multi‑camera setups
