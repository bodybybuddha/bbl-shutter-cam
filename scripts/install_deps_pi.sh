#!/usr/bin/env bash
set -euo pipefail

sudo apt update
sudo apt install -y \
  bluez \
  python3 \
  python3-venv \
  rpicam-apps
