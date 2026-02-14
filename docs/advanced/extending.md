---
layout: page
title: Contributing & Development
nav_order: 3
parent: Advanced
---

# Contributing & Development

Extend and improve `bbl-shutter-cam`.

## Overview

This project is open-source and welcomes contributions. For comprehensive developer setup instructions, see [**CONTRIBUTING.md**](../../CONTRIBUTING.md) at the project root.

This guide covers:
- Local development setup
- Code structure and patterns
- Adding features
- Submitting changes

For VSCode setup, tasks, and testing workflows, see [CONTRIBUTING.md](../../CONTRIBUTING.md).

---

## Development Setup

### 1. Clone Repository

```bash
git clone https://github.com/bodybybuddha/bbl-shutter-cam.git
cd bbl-shutter-cam
```

### 2. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
```

On Windows:
```cmd
python -m venv venv
venv\Scripts\activate
```

### 3. Install Development Dependencies

```bash
pip install -e ".[dev]"
```

This installs the package in editable mode plus dev tools (pytest, pylint, mypy, black).

### 4. Verify Setup

```bash
# Check CLI
bbl-shutter-cam --help

# Run tests
pytest tests/ -v

# Lint code
pylint src/bbl_shutter_cam/
```

---

## Code Structure

```
src/bbl_shutter_cam/
├── __init__.py              # Package metadata
├── cli.py                   # Command-line interface
├── discover.py              # BLE device discovery & capture orchestration
├── ble.py                   # Bluetooth Low Energy utilities
├── config.py                # Configuration file handling
├── camera.py                # Camera capture (rpicam-still wrapper)
├── util.py                  # Common utilities
└── logging_config.py        # Logging setup
```

### Module Responsibilities

**cli.py** - Command parsing and subcommand routing
- `main()` - Entry point, argument parsing
- `_cmd_scan()` - BLE device scanning
- `_cmd_setup()` - Interactive device setup
- `_cmd_debug()` - Signal discovery
- `_cmd_run()` - Photo capture

**discover.py** - Core business logic
- `run_profile()` - Main event loop, triggers photo capture on signals
- `learn_notify_uuid()` - Interactive Bluetooth setup
- `debug_signals()` - Signal discovery and logging
- `_update_config_with_signals()` - Save discovered signals to config

**config.py** - Configuration management
- `load_config()` - Load user's main config file
- `load_profile()` - Load specific printer profile
- `get_trigger_events()` - Load trigger signals from config
- `get_event_trigger_bytes()` - Filter and convert signals to bytes
- `update_profile_device_fields()` - Save device settings

**ble.py** - Hardware abstraction
- `BLEClient` class - Async Bluetooth connection wrapper
- `scan()` - Find nearby BLE devices
- `connect()` - Establish connection
- `start_notify()` - Subscribe to characteristic updates

**camera.py** - Camera operations
- `capture()` - Trigger photo using rpicam-still

---

## Architecture Patterns

### Asyncio First

All BLE operations are async:

```python
# Good
async def run_profile(profile):
    async with BLEClient(mac_address) as client:
        await client.start_notify(uuid, callback)

# Avoid
client = BLEClient(mac_address)  # Won't work, needs await
```

### Config-Driven, Not Hardcoded

Store configuration in TOML, not code constants:

```python
# Good
trigger_events = get_trigger_events(profile)
for event in trigger_events:
    if event.get("capture"):
        # Process event

# Avoid
PRESS_BYTES = bytes.fromhex("4000")  # Hardcoded!
```

### Profile-Based Isolation

Each printer has its config profile:

```toml
[profiles.office-p1s]
device = { mac = "AA:BB:CC:DD:EE:FF", ... }

[profiles.garage-x1c]
device = { mac = "11:22:33:44:55:66", ... }
```

---

## Common Tasks

### Add New CLI Subcommand

1. Add argument parser in `cli.py`:

```python
# In main(), add subparsers section:
debug_parser = subparsers.add_parser("tune")
debug_parser.add_argument("--profile", required=True)
debug_parser.add_argument("--option", default="value")
debug_parser.set_defaults(func=_cmd_tune)
```

2. Implement handler function:

```python
def _cmd_tune(args):
    """Handle tune subcommand."""
    profile = config.load_profile(args.profile)
    asyncio.run(discover.tune_profile(profile, args.option))
```

3. Implement logic in `discover.py`:

```python
async def tune_profile(profile, option):
    """Interactive camera tuning."""
    # Your logic here
    pass
```

### Modify BLE Signal Handling

Current signal handling in `discover.py` `run_profile()`:

```python
trigger_events = get_trigger_events(profile)
trigger_map = {}
for event in trigger_events:
    trigger_bytes = bytes.fromhex(event.get("hex", ""))
    trigger_map[trigger_bytes] = event

# On notification:
if data in trigger_map:
    event = trigger_map[data]
    if event.get("capture"):
        await camera.capture(profile)
```

To add a filter (e.g., ignore glitches below 100ms):

```python
# In run_profile():
last_trigger = 0
while running:
    async for data in client.iterate_notify():
        now = time.time()
        if (now - last_trigger) < 0.1:  # 100ms debounce
            continue
        last_trigger = now
        if data in trigger_map and trigger_map[data].get("capture"):
            await camera.capture(profile)
```

### Add Configuration Option

1. Update TOML schema in docs (`docs/user-guide/profiles.md`)
2. Add to config loading (`config.py`):

```python
def load_profile(name):
    profile = config.load_config()
    profile_data = profile[f"profiles.{name}"]
    my_option = profile_data.get("my_key", "default_value")
    return profile_data
```

3. Use in `discover.py`:

```python
async def run_profile(profile):
    my_option = profile.get("my_key", "default_value")
    # Use option...
```

---

## Testing

### Run All Tests

```bash
pytest tests/ -v
```

### Run Specific Test File

```bash
pytest tests/test_config.py -v
```

### Check Coverage

```bash
pytest tests/ --cov=src/bbl_shutter_cam
```

### Adding New Tests

Create test file in `tests/`:

```python
# tests/test_myfeature.py
import pytest
from bbl_shutter_cam import myfeature

def test_something():
    result = myfeature.my_function()
    assert result == expected

@pytest.mark.asyncio
async def test_async_something():
    result = await myfeature.my_async_function()
    assert result == expected
```

Run:

```bash
pytest tests/test_myfeature.py -v
```

---

## Code Quality

### Linting

```bash
pylint src/bbl_shutter_cam/
```

Fix common issues:

```bash
black src/bbl_shutter_cam/  # Auto-format
```

### Type Checking

```bash
mypy src/bbl_shutter_cam/ --ignore-missing-imports
```

### Before Committing

```bash
# Format code
black src/bbl_shutter_cam/

# Lint
pylint src/bbl_shutter_cam/

# Run tests
pytest tests/ -v

# Type check
mypy src/bbl_shutter_cam/ --ignore-missing-imports
```

---

## Git Workflow

### Create Feature Branch

```bash
git checkout -b feature/my-feature
# or
git checkout -b fix/bug-name
```

### Make Changes

```bash
git add src/bbl_shutter_cam/my_file.py
git commit -m "feat: add new feature

Detailed description of change.
"
```

**Commit message format:**
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation
- `test:` - Tests
- `refactor:` - Code refactoring

### Push and Create Pull Request

```bash
git push origin feature/my-feature
```

Then open pull request on GitHub.

---

## Release Process

1. Update version in `pyproject.toml`
2. Update `CHANGELOG.md` (if used)
3. Create git tag:

```bash
git tag -a v0.2.0 -m "Version 0.2.0 release"
git push origin v0.2.0
```

4. Create GitHub Release with release notes
5. Build distribution:

```bash
pip install build
python -m build
```

---

## Documentation

When adding features:

1. Update code with docstrings:

```python
def my_function(param1: str) -> bool:
    """Short description.

    Longer description explaining the function's behavior,
    parameters, and return value.

    Args:
        param1: Description of param1

    Returns:
        Description of return value
    """
    pass
```

2. Update user documentation in `docs/`
3. Add FAQ entry if commonly needed

---

## Building Standalone Executables

Want to distribute `bbl-shutter-cam` as a standalone application without requiring Python?

See the [Building Executables Guide](building-executables.md) for detailed instructions on:
- Creating executables for Windows, macOS, and Linux
- Using PyInstaller for cross-platform builds
- Distribution and sharing

Quick start:

```bash
# macOS / Linux
./scripts/build.sh

# Windows
scripts\build.bat
```

Your executable will be in the `dist/` folder.

---

## Reporting Issues

Use GitHub Issues to report bugs or suggest features:

1. Search existing issues first
2. Provide:
   - Steps to reproduce
   - Expected behavior
   - Actual behavior
   - Environment (Pi model, OS, camera, etc.)

---

## Questions?

- Check [FAQ](../faq.md)
- Review [Troubleshooting](../troubleshooting.md)
- Open GitHub discussion or issue

---

**Thank you for contributing!**
