from __future__ import annotations

import shutil
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT / "src"
ADDON_NAME = "blender_plugin_starter"
ADDON_DIR = SRC_DIR / ADDON_NAME
DIST_DIR = ROOT / "dist"
OUTPUT_ZIP = DIST_DIR / f"{ADDON_NAME}.zip"

EXCLUDE_DIRS = {"__pycache__", ".mypy_cache", ".pytest_cache", ".ruff_cache"}
EXCLUDE_SUFFIXES = {".pyc", ".pyo"}


def should_include(path: Path) -> bool:
    if any(part in EXCLUDE_DIRS for part in path.parts):
        return False
    if path.suffix in EXCLUDE_SUFFIXES:
        return False
    return True


def main() -> None:
    if not ADDON_DIR.exists():
        raise FileNotFoundError(f"Addon source not found: {ADDON_DIR}")

    DIST_DIR.mkdir(exist_ok=True)
    if OUTPUT_ZIP.exists():
        OUTPUT_ZIP.unlink()

    with zipfile.ZipFile(OUTPUT_ZIP, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in ADDON_DIR.rglob("*"):
            if path.is_file() and should_include(path.relative_to(ADDON_DIR)):
                archive.write(path, path.relative_to(SRC_DIR))

    print(f"Packaged addon: {OUTPUT_ZIP}")


if __name__ == "__main__":
    main()
