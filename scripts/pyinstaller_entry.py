"""PyInstaller entrypoint wrapper.

PyInstaller executes the provided script as "__main__". If we point it directly at
"bbl_shutter_cam/cli.py", then relative imports ("from . …") fail because the
module is no longer executed as part of a package.

This wrapper imports the package CLI normally and calls main().
"""

from __future__ import annotations

from bbl_shutter_cam.cli import main


if __name__ == "__main__":
    raise SystemExit(main())
