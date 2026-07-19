from __future__ import annotations

import bpy

from .operators import STARTER_OT_add_marker_cube
from .panels import STARTER_PT_main_panel
from .preferences import STARTER_AddonPreferences


CLASSES = (
    STARTER_AddonPreferences,
    STARTER_OT_add_marker_cube,
    STARTER_PT_main_panel,
)


def register() -> None:
    for cls in CLASSES:
        bpy.utils.register_class(cls)


def unregister() -> None:
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
