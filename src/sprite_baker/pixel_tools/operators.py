import bpy

from .materials import SBK_OT_create_pixel_material
from .viewport_display import set_viewport_render_preview
from .viewport_preview import (
    remove_viewport_pixel_preview,
    setup_viewport_pixel_preview,
    set_viewport_pixel_transform,
)


class SBK_OT_setup_viewport_pixel_preview(bpy.types.Operator):
    bl_idname = "sprite_baker.setup_viewport_pixel_preview"
    bl_label = "设置像素预览"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        settings = context.scene.sprite_baker_settings
        preview_scale = active_preview_scale(settings)
        set_viewport_render_preview(context, rendered=True)
        try:
            setup_viewport_pixel_preview(
                context.scene,
                preview_scale,
                settings.pixel_preview_offset_x,
                settings.pixel_preview_offset_y,
            )
        except RuntimeError as error:
            self.report({"WARNING"}, str(error))
            return {"CANCELLED"}
        set_viewport_pixel_transform(
            context.scene,
            preview_scale,
            settings.pixel_preview_offset_x,
            settings.pixel_preview_offset_y,
        )
        self.report({"INFO"}, "像素预览已设置。")
        return {"FINISHED"}


class SBK_OT_update_viewport_preview_resolution(bpy.types.Operator):
    bl_idname = "sprite_baker.update_viewport_preview_resolution"
    bl_label = "更新像素预览"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        settings = context.scene.sprite_baker_settings
        preview_scale = active_preview_scale(settings)
        updated = set_viewport_pixel_transform(
            context.scene,
            preview_scale,
            settings.pixel_preview_offset_x,
            settings.pixel_preview_offset_y,
        )
        if not updated:
            self.report({"WARNING"}, "请先设置像素预览。")
            return {"CANCELLED"}
        self.report({"INFO"}, "像素预览已更新。")
        return {"FINISHED"}


class SBK_OT_remove_viewport_pixel_preview(bpy.types.Operator):
    bl_idname = "sprite_baker.remove_viewport_pixel_preview"
    bl_label = "移除像素预览"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        removed = remove_viewport_pixel_preview(context.scene)
        self.report({"INFO"}, f"已移除 {removed} 个像素预览节点。")
        return {"FINISHED"}


def active_preview_scale(settings):
    if settings.pixel_canvas_preset == "CUSTOM":
        return settings.pixel_preview_scale
    return 1.0


CLASSES = (
    SBK_OT_setup_viewport_pixel_preview,
    SBK_OT_update_viewport_preview_resolution,
    SBK_OT_remove_viewport_pixel_preview,
    SBK_OT_create_pixel_material,
)
