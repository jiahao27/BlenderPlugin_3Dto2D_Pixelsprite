import bpy

from . import pixel_tools
from .operators import (
    SBK_OT_add_action,
    SBK_OT_add_export_item,
    SBK_OT_create_bake_camera,
    SBK_OT_clear_pixel_grid,
    SBK_OT_export,
    SBK_OT_generate_directions,
    SBK_OT_preview,
    SBK_OT_refresh_pixel_grid,
    SBK_OT_remove_action,
    SBK_OT_remove_direction,
    SBK_OT_remove_export_item,
    SBK_OT_validate,
)
from .properties import (
    SBK_ActionSlot,
    SBK_DirectionSlot,
    SBK_ExportItem,
    SBK_MaskAssignment,
    SBK_Settings,
    register_properties,
    unregister_properties,
)
from .ui import (
    SBK_PT_camera_frames,
    SBK_PT_export_items,
    SBK_PT_mask_assignment,
    SBK_PT_passes,
    SBK_PT_pixel_effect,
    SBK_PT_preview_export,
    SBK_PT_project_settings,
    SBK_UL_actions,
    SBK_UL_directions,
    SBK_UL_export_items,
)


CLASSES = (
    SBK_MaskAssignment,
    SBK_ActionSlot,
    SBK_DirectionSlot,
    SBK_ExportItem,
    SBK_Settings,
    SBK_UL_export_items,
    SBK_UL_actions,
    SBK_UL_directions,
    SBK_OT_add_export_item,
    SBK_OT_remove_export_item,
    SBK_OT_add_action,
    SBK_OT_remove_action,
    SBK_OT_generate_directions,
    SBK_OT_remove_direction,
    SBK_OT_create_bake_camera,
    SBK_OT_refresh_pixel_grid,
    SBK_OT_clear_pixel_grid,
    SBK_OT_validate,
    SBK_OT_preview,
    SBK_OT_export,
    SBK_PT_project_settings,
    SBK_PT_camera_frames,
    SBK_PT_export_items,
    SBK_PT_pixel_effect,
    SBK_PT_passes,
    SBK_PT_mask_assignment,
    SBK_PT_preview_export,
    *pixel_tools.CLASSES,
)


def register():
    for cls in CLASSES:
        bpy.utils.register_class(cls)
    register_properties()
    pixel_tools.register_properties()


def unregister():
    pixel_tools.unregister_properties()
    unregister_properties()
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
