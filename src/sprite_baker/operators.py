import traceback

import bpy

from .baker import SpriteBaker
from .validation import get_active_item, parse_custom_directions, validate_settings


class SBK_OT_add_export_item(bpy.types.Operator):
    bl_idname = "sprite_baker.add_export_item"
    bl_label = "Add Export Item"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        settings = context.scene.sprite_baker_settings
        item = settings.export_items.add()
        item.name = context.object.name if context.object else "Sprite"
        if context.object:
            item.target_object = context.object
        settings.active_export_item_index = len(settings.export_items) - 1
        generate_directions_for_item(item)
        return {"FINISHED"}


class SBK_OT_remove_export_item(bpy.types.Operator):
    bl_idname = "sprite_baker.remove_export_item"
    bl_label = "Remove Export Item"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        settings = context.scene.sprite_baker_settings
        if settings.export_items:
            settings.export_items.remove(settings.active_export_item_index)
            settings.active_export_item_index = max(0, settings.active_export_item_index - 1)
        return {"FINISHED"}


class SBK_OT_add_action(bpy.types.Operator):
    bl_idname = "sprite_baker.add_action"
    bl_label = "Add Action"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        item = get_active_item(context.scene.sprite_baker_settings)
        if item is None:
            return {"CANCELLED"}
        slot = item.actions.add()
        source = item.armature or item.target_object
        if source and source.animation_data:
            slot.action = source.animation_data.action
        item.active_action_index = len(item.actions) - 1
        return {"FINISHED"}


class SBK_OT_remove_action(bpy.types.Operator):
    bl_idname = "sprite_baker.remove_action"
    bl_label = "Remove Action"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        item = get_active_item(context.scene.sprite_baker_settings)
        if item and item.actions:
            item.actions.remove(item.active_action_index)
            item.active_action_index = max(0, item.active_action_index - 1)
        return {"FINISHED"}


class SBK_OT_generate_directions(bpy.types.Operator):
    bl_idname = "sprite_baker.generate_directions"
    bl_label = "Generate Directions"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        item = get_active_item(context.scene.sprite_baker_settings)
        if item is None:
            return {"CANCELLED"}
        try:
            generate_directions_for_item(item)
        except ValueError as exc:
            self.report({"ERROR"}, str(exc))
            return {"CANCELLED"}
        return {"FINISHED"}


class SBK_OT_remove_direction(bpy.types.Operator):
    bl_idname = "sprite_baker.remove_direction"
    bl_label = "Remove Direction"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        item = get_active_item(context.scene.sprite_baker_settings)
        if item and item.directions:
            item.directions.remove(item.active_direction_index)
            item.active_direction_index = max(0, item.active_direction_index - 1)
        return {"FINISHED"}


class SBK_OT_validate(bpy.types.Operator):
    bl_idname = "sprite_baker.validate"
    bl_label = "Validate Sprite Bake"
    bl_options = {"REGISTER"}

    def execute(self, context):
        errors = validate_settings(context)
        if errors:
            for error in errors:
                self.report({"ERROR"}, error)
            return {"CANCELLED"}
        self.report({"INFO"}, "Sprite Baker validation passed.")
        return {"FINISHED"}


class SBK_OT_preview(bpy.types.Operator):
    bl_idname = "sprite_baker.preview"
    bl_label = "Preview Current Frame"
    bl_options = {"REGISTER"}

    def execute(self, context):
        errors = validate_settings(context, preview=True)
        if errors:
            for error in errors:
                self.report({"ERROR"}, error)
            return {"CANCELLED"}
        try:
            files = SpriteBaker(context).render_preview()
        except Exception as exc:
            traceback.print_exc()
            self.report({"ERROR"}, f"Preview failed: {exc}")
            return {"CANCELLED"}
        self.report({"INFO"}, f"Preview written: {', '.join(files)}")
        return {"FINISHED"}


class SBK_OT_export(bpy.types.Operator):
    bl_idname = "sprite_baker.export"
    bl_label = "Export Sprite Sequences"
    bl_options = {"REGISTER"}

    def execute(self, context):
        errors = validate_settings(context)
        if errors:
            for error in errors:
                self.report({"ERROR"}, error)
            return {"CANCELLED"}
        try:
            count = SpriteBaker(context).export_all()
        except Exception as exc:
            traceback.print_exc()
            self.report({"ERROR"}, f"Export failed: {exc}")
            return {"CANCELLED"}
        self.report({"INFO"}, f"Sprite Baker exported {count} frame pass files.")
        return {"FINISHED"}


def generate_directions_for_item(item):
    if item.direction_preset == "SINGLE":
        angles = [0.0]
    elif item.direction_preset == "FOUR":
        angles = [0.0, 90.0, 180.0, 270.0]
    elif item.direction_preset == "EIGHT":
        angles = [0.0, 45.0, 90.0, 135.0, 180.0, 225.0, 270.0, 315.0]
    else:
        angles = parse_custom_directions(item.custom_directions)

    item.directions.clear()
    for angle in angles:
        slot = item.directions.add()
        normalized = angle % 360.0
        slot.angle = normalized
        slot.name = f"dir_{int(round(normalized)):03d}"
    item.active_direction_index = 0
