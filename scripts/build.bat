@echo off
REM Build script for bbl-shutter-cam on Windows

setlocal enabledelayedexpansion

echo.
echo Building bbl-shutter-cam for Windows...
echo.

REM Check if PyInstaller is installed
python -m pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo PyInstaller not found. Installing dev dependencies...
    python -m pip install -e ".[dev]"
)

REM Clean old builds
if exist dist (
    echo Cleaning old build files...
    rmdir /s /q dist
)
if exist build (
    rmdir /s /q build
)

REM Build executable
echo Building executable...
python -m PyInstaller ^
    --onefile ^
    --console ^
    --name bbl-shutter-cam ^
    --paths src ^
    --add-data src/bbl_shutter_cam;bbl_shutter_cam ^
    --hidden-import=bleak ^
    --hidden-import=tomlkit ^
    scripts/pyinstaller_entry.py

echo.
if exist "dist\bbl-shutter-cam.exe" (
    echo Build complete!
    echo.
    echo Executable created: dist\bbl-shutter-cam.exe
    echo.
    echo To use it:
    echo   1. Copy 'dist\bbl-shutter-cam.exe' to your PATH or preferred location
    echo   2. Run: dist\bbl-shutter-cam.exe --help
) else (
    echo Build may have failed - no executable found in dist\
    exit /b 1
)

endlocal
