---
layout: page
title: Auto-Start with Systemd
nav_order: 2
parent: Advanced
---

# Auto-Start with Systemd

Run `bbl-shutter-cam` automatically on Pi boot.

## Overview

Systemd services ensure `bbl-shutter-cam` starts and restarts automatically.

## User Service (Recommended for Development)

Create a user-level service (no sudo needed):

### 1. Create Service File

```bash
mkdir -p ~/.config/systemd/user

cat > ~/.config/systemd/user/bbl-shutter-cam.service << 'EOF'
[Unit]
Description=BBL Shutter Cam Time-Lapse Capture
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/bbl-shutter-cam
ExecStart=/home/pi/bbl-shutter-cam/venv/bin/bbl-shutter-cam run --profile my-printer --log-file %h/bbl.log
Restart=always
RestartSec=10

[Install]
WantedBy=default.target
EOF
```

**Edit:**
- Change `my-printer` to your profile name
- Change `/home/pi` to your home directory if different

### 2. Enable & Start

```bash
systemctl --user daemon-reload
systemctl --user enable bbl-shutter-cam
systemctl --user start bbl-shutter-cam
```

### 3. Check Status

```bash
systemctl --user status bbl-shutter-cam
```

**Expected output:**
```
● bbl-shutter-cam.service - BBL Shutter Cam Time-Lapse Capture
     Loaded: loaded (/home/pi/.config/systemd/user/bbl-shutter-cam.service; enabled; preset: enabled)
     Active: active (running) since Thu 2026-02-14 10:30:45 UTC; 5min ago
   Main PID: 1234 (bbl-shutter-cam)
      Tasks: 5
     Memory: 15.2M
        CGroup: /user.slice/user-1000.slice/user@1000.service/app.slice/bbl-shutter-cam.service
                └─1234 /home/pi/bbl-shutter-cam/venv/bin/bbl-shutter-cam run ...
```

### 4. View Logs

```bash
# Real-time
journalctl --user -u bbl-shutter-cam -f

# Last 50 lines
journalctl --user -u bbl-shutter-cam -n 50
```

### 5. Stop/Restart

```bash
# Stop
systemctl --user stop bbl-shutter-cam

# Restart
systemctl --user restart bbl-shutter-cam

# Check next boot
systemctl --user is-enabled bbl-shutter-cam
# Output: enabled
```

---

## System Service (Optional - for System-Wide)

For system-wide installation (requires sudo):

```bash
sudo tee /etc/systemd/system/bbl-shutter-cam.service > /dev/null << 'EOF'
[Unit]
Description=BBL Shutter Cam Time-Lapse Capture
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/bbl-shutter-cam
ExecStart=/home/pi/bbl-shutter-cam/venv/bin/bbl-shutter-cam run --profile my-printer --log-file /home/pi/bbl.log
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
```

Then:

```bash
sudo systemctl daemon-reload
sudo systemctl enable bbl-shutter-cam
sudo systemctl start bbl-shutter-cam
```

---

## Multiple Profiles

Running multiple printer profiles with systemd:

### Create Separate Services

```bash
# User service for multiple profiles
cat > ~/.config/systemd/user/bbl-shutter-cam-p1s.service << 'EOF'
[Unit]
Description=BBL Shutter Cam - P1S Office
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/bbl-shutter-cam
ExecStart=/home/pi/bbl-shutter-cam/venv/bin/bbl-shutter-cam run --profile p1s-office --log-file %h/bbl-p1s.log
Restart=always
RestartSec=10

[Install]
WantedBy=default.target
EOF

cat > ~/.config/systemd/user/bbl-shutter-cam-x1c.service << 'EOF'
[Unit]
Description=BBL Shutter Cam - X1C Garage
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/bbl-shutter-cam
ExecStart=/home/pi/bbl-shutter-cam/venv/bin/bbl-shutter-cam run --profile x1c-garage --log-file %h/bbl-x1c.log
Restart=always
RestartSec=10

[Install]
WantedBy=default.target
EOF
```

Enable both:

```bash
systemctl --user daemon-reload
systemctl --user enable bbl-shutter-cam-p1s bbl-shutter-cam-x1c
systemctl --user start bbl-shutter-cam-p1s bbl-shutter-cam-x1c
```

Check both:

```bash
systemctl --user status bbl-shutter-cam-p1s bbl-shutter-cam-x1c
```

---

## Troubleshooting

### Service Won't Start

```bash
journalctl --user -u bbl-shutter-cam -n 50
```

Look for error messages. Common issues:
- Profile name typo
- Working directory wrong
- venv path incorrect

### Service Keeps Restarting

Check logs for capture errors. Likely:
- Camera not available
- Bluetooth connection issues
- Output directory permission problems

### Disable Service

```bash
systemctl --user disable bbl-shutter-cam
systemctl --user stop bbl-shutter-cam
```

### Uninstall Service

```bash
rm ~/.config/systemd/user/bbl-shutter-cam.service
systemctl --user daemon-reload
```

---

## Auto-Start on Boot

Systemd automatically starts enabled user services when user logs in.

For headless Pi that boots without login:

```bash
# Enable "linger" (for background startup without login)
sudo loginctl enable-linger pi
```

---

## Next Steps

- [Headless Operation](headless-operation.md)
- [Troubleshooting](../troubleshooting.md)
