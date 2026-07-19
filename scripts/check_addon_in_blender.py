from __future__ import annotations

import importlib
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT / "src"
ADDON_NAME = "sprite_baker"


def main() -> None:
    sys.path.insert(0, str(SRC_DIR))

    addon = importlib.import_module(ADDON_NAME)
    addon.register()
    addon.unregister()

    print(f"Blender add-on registration check passed: {ADDON_NAME}")


if __name__ == "__main__":
    main()
