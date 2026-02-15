#!/bin/bash
# Build script for bbl-shutter-cam
# Detects platform and builds appropriate executable

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Determine platform
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    PLATFORM="linux"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    PLATFORM="macos"
elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin"* ]]; then
    PLATFORM="windows"
else
    PLATFORM="unknown"
fi

echo "📦 Building bbl-shutter-cam for $PLATFORM..."
echo ""

# Check if PyInstaller is installed
if ! python3 -m pip show pyinstaller > /dev/null 2>&1; then
    echo "❌ PyInstaller not found. Installing dev dependencies..."
    python3 -m pip install -e ".[dev]"
fi

# Clean old builds
if [ -d "dist" ]; then
    echo "🧹 Cleaning old build files..."
    rm -rf dist/ build/
fi

# Build executable
echo "🔨 Building executable..."
python3 -m PyInstaller \
    --onefile \
    --console \
    --name bbl-shutter-cam \
    --paths src \
    --add-data src/bbl_shutter_cam:bbl_shutter_cam \
    --hidden-import=bleak \
    --hidden-import=tomlkit \
    scripts/pyinstaller_entry.py

echo ""
echo "✅ Build complete!"
echo ""

# Show output location
if [ -f "dist/bbl-shutter-cam" ]; then
    echo "📍 Executable created: dist/bbl-shutter-cam"
    echo ""
    echo "To use it:"
    echo "  1. Copy 'dist/bbl-shutter-cam' to your PATH or preferred location"
    echo "  2. Make it executable: chmod +x dist/bbl-shutter-cam"
    echo "  3. Run: ./dist/bbl-shutter-cam --help"
elif [ -f "dist/bbl-shutter-cam.exe" ]; then
    echo "📍 Executable created: dist/bbl-shutter-cam.exe"
    echo ""
    echo "To use it:"
    echo "  1. Copy 'dist/bbl-shutter-cam.exe' to your PATH or preferred location"
    echo "  2. Run: dist\\bbl-shutter-cam.exe --help"
else
    echo "❌ Build may have failed - no executable found in dist/"
    exit 1
fi
