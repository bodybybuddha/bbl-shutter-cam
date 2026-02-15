# Building Standalone Executables

This guide covers building `bbl-shutter-cam` into standalone executables for Windows, macOS, and Linux.

## What is PyInstaller?

PyInstaller packages your Python application into a single executable that doesn't require Python to be installed on the user's system. Users can download and run the executable directly.

## Prerequisites

1. **Python 3.9+** installed
2. **PyInstaller** (installed as part of dev dependencies)

## Quick Start

### macOS / Linux

```bash
# Install dev dependencies (includes PyInstaller)
pip install -e ".[dev]"

# Run the build script
./scripts/build.sh

# Find your executable at: dist/bbl-shutter-cam
```

### Windows

```cmd
# Install dev dependencies
pip install -e ".[dev]"

# Run the build script
scripts\build.bat

# Find your executable at: dist\bbl-shutter-cam.exe
```

## Manual Build (All Platforms)

If the scripts don't work for your setup:

```bash
# Install dependencies
pip install -e ".[dev]"

# Build the executable (preferred)
pyinstaller bbl-shutter-cam.spec

# Executable will be in dist/ folder
```

## After Building

### macOS / Linux

```bash
# Make it executable (usually already is)
chmod +x dist/bbl-shutter-cam

# Test it
./dist/bbl-shutter-cam --help

# Install to system (optional)
sudo cp dist/bbl-shutter-cam /usr/local/bin/bbl-shutter-cam
```

### Windows

```cmd
# Test it
dist\bbl-shutter-cam.exe --help

# Install to PATH (optional)
# Copy dist\bbl-shutter-cam.exe to a folder in your PATH
```

## Distribution

For sharing with others:

1. **Build the executable** using the steps above
2. **Test it thoroughly** - make sure configs are portable
3. **Compress for distribution**:
   - **macOS/Linux**: `tar -czf bbl-shutter-cam-linux-x64.tar.gz dist/bbl-shutter-cam`
   - **Windows**: `zip -r bbl-shutter-cam-windows.zip dist/bbl-shutter-cam.exe`

If you only need Raspberry Pi binaries, use the GitHub Releases page. Each release automatically builds and attaches:
- `bbl-shutter-cam-<version>-linux-arm64`
- `bbl-shutter-cam-<version>-linux-armv7`

## Cross-Platform Building (CI/CD)

Automated builds run on GitHub Actions for Raspberry Pi targets. When a GitHub Release is published, the workflow builds and uploads arm64 and armv7 binaries to the release.

## Troubleshooting

### "PyInstaller not found"

```bash
pip install pyinstaller
```

### "Module not found" errors

Add the module to `hiddenimports` in `bbl-shutter-cam.spec`:

```python
hiddenimports=['bleak', 'tomlkit', 'your_module_here'],
```

### "attempted relative import with no known parent package"

This usually happens if you freeze `src/bbl_shutter_cam/cli.py` directly.
Build using the provided spec or wrapper entry script instead:

```bash
python -m PyInstaller --onefile --console --name bbl-shutter-cam --paths src scripts/pyinstaller_entry.py
```

### File size is large

This is normal - PyInstaller bundles Python + all dependencies. Try:

```bash
pyinstaller --onefile --strip bbl-shutter-cam.spec
```

### macOS "App can't be opened" error

```bash
chmod +x dist/bbl-shutter-cam
codesign --deep --force --verify --verbose --sign - dist/bbl-shutter-cam
```

## Notes

- **Config files** are stored in `~/.config/bbl-shutter-cam/` and will work across all platforms
- **Executable is standalone** - no Python installation needed by end users
- **Binary size**: Each executable is ~50-100MB (includes Python runtime)
- **macOS executable**: This is a regular CLI executable, not a `.app` bundle
---

## Testing Locally Before Release

To test the binary thoroughly before publishing a release:

### Using VS Code Tasks

1. **Build**: Press `Ctrl+Shift+B` (or `Cmd+Shift+B` on Mac) and select "Build executable"
2. **Test**: Run task "Test local binary" to verify it launches
3. **Build and test**: Run task "Build and test binary" to do both in sequence

### Manual Testing Workflow

```bash
# 1. Build the executable
./scripts/build.sh

# 2. Quick smoke test
./dist/bbl-shutter-cam --help

# 3. Test with a real config (dry-run)
sudo ./dist/bbl-shutter-cam --config ~/.config/bbl-shutter-cam/config.toml \
  run --profile your-profile --dry-run --verbose

# 4. Test scan functionality
sudo ./dist/bbl-shutter-cam scan --name BBL_SHUTTER --timeout 10

# 5. Full integration test (optional)
# Create a test directory with a test config
mkdir -p binarytesting
cp ~/.config/bbl-shutter-cam/config.toml binarytesting/
sudo ./dist/bbl-shutter-cam --config binarytesting/config.toml \
  run --profile your-profile --dry-run --verbose
```

### Pre-Release Checklist

Before tagging a release:

- [ ] Binary builds without errors
- [ ] `--help` displays correctly
- [ ] `scan` command works
- [ ] `run --dry-run` connects and receives shutter signals
- [ ] Config parsing works (no errors on valid config)
- [ ] All quality gates pass (tests, lint, type check)
- [ ] Documentation is up to date
- [ ] `CHANGELOG.md` updated with release notes

### Comparing with Released Binaries

To compare your local build with a GitHub release:

```bash
# Download release binary
curl -L -o bbl-shutter-cam-release \
  https://github.com/bodybybuddha/bbl-shutter-cam/releases/download/v1.0.1/bbl-shutter-cam-v1.0.1-linux-arm64

# Compare file sizes
ls -lh dist/bbl-shutter-cam bbl-shutter-cam-release

# Test both
chmod +x bbl-shutter-cam-release
./bbl-shutter-cam-release --help
./dist/bbl-shutter-cam --help
```
