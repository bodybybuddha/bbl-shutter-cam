---
layout: page
title: Headless Operation
nav_order: 1
parent: Advanced
---

# Headless Operation

Running `bbl-shutter-cam` without a monitor or keyboard.

## Remote Access

### SSH (Terminal)

Access your Pi remotely:

```bash
# From your PC/Mac
ssh pi@raspberrypi.local
# Or with IP:
ssh pi@192.168.1.100
```

### SFTP (File Transfer)

Download photos from your Pi:

```bash
# From your PC
sftp pi@raspberrypi.local
> cd captures/my-printer
> get *.jpg ./local-folder
> quit
```

Or use SCP:

```bash
scp -r pi@raspberrypi.local:captures/my-printer .
```

### Web Transfer (Future)

Planned for v1.0: Web-based photo gallery and transfer.

---

## Running in Background

### Method 1: tmux / screen

Persistent session that survives disconnect:

```bash
tmux new-session -d -s bbl-cam 'cd ~/bbl-shutter-cam && source venv/bin/activate && bbl-shutter-cam run --profile my-printer'

# Later, reconnect:
tmux attach -t bbl-cam

# Stop:
tmux kill-session -t bbl-cam
```

### Method 2: nohup

Simple background execution:

```bash
nohup ~/bbl-shutter-cam/venv/bin/bbl-shutter-cam run --profile my-printer > ~/bbl.log 2>&1 &
```

### Method 3: systemd (Recommended)

→ See [Auto-Start with Systemd](systemd-service.md)

---

## Logging to File

Capture output for review:

```bash
bbl-shutter-cam run --profile my-printer \
  --log-file ~/bbl.log \
  --log-level info
```

Monitor in real-time:

```bash
# From another SSH session
tail -f ~/bbl.log
```

---

## Headless Printing Environment

### Power Management

Keep Pi running through long prints:

```bash
# Disable sleep
sudo systemctl mask sleep.target suspend.target hibernate.target hybernate.target

# Or less aggressively:
sudo nano /etc/systemd/sleep.conf
# AllowSuspend=no
# AllowHibernation=no
```

### Network Stability

If using Wi-Fi (Ethernet preferred):

```bash
# Check connection
ping 8.8.8.8

# Monitor signal strength
iwconfig wlan0 | grep Signal
```

---

## Auto-Start on Boot

→ See [Auto-Start with Systemd](systemd-service.md)

---

## Monitoring & Alerts

(Planned for future versions)

- Email notifications on error
- Remote status dashboard
- Auto-restart on crash

---

## Next Steps

- [Auto-Start with Systemd](systemd-service.md)
- [Troubleshooting](../troubleshooting.md)
