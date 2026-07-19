from __future__ import annotations

import bpy


def get_addon_preferences(context: bpy.types.Context) -> bpy.types.AddonPreferences | None:
    addon = context.preferences.addons.get(__package__)
    if addon is None:
        return None
    return addon.preferences
