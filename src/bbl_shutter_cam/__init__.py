"""bbl-shutter-cam: Bluetooth-triggered time-lapse capture for Raspberry Pi.

A command-line application that listens for Bluetooth shutter signals from a
Bambu Lab CyberBrick Time-Lapse Kit (BBL_SHUTTER) and automatically captures
photos using a Raspberry Pi camera.

Key components:
    - `cli`: Command-line interface and argument parsing
    - `discover`: BLE device discovery and profile setup
    - `ble`: Bluetooth Low Energy utilities (connection, notification handling)
    - `camera`: Camera capture logic (rpicam-still wrapper)
    - `config`: Configuration file handling (TOML-based)
    - `util`: Logging and utility functions
"""

__version__ = "1.0.1"
__author__ = "Casa Taylor"
__license__ = "MIT"
