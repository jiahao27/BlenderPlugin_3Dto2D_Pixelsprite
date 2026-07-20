import traceback

import bpy

from .baker import SpriteBaker
from .camera import configure_camera, make_visible_bake_camera, object_bounds
from .pixel_tools.grid_images import attach_grid_background, clear_grid_backgrounds
from .validation import get_active_item, parse_custom_directions, target_objects, validate_settings


class SBK_OT_add_export_item(bpy.types.Operator):
    bl_idname = "sprite_baker.add_export_item"
    bl_label = "添加烘焙目标"
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
    bl_label = "删除烘焙目标"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        settings = context.scene.sprite_baker_settings
        if settings.export_items:
            settings.export_items.remove(settings.active_export_item_index)
            settings.active_export_item_index = max(0, settings.active_export_item_index - 1)
        return {"FINISHED"}


class SBK_OT_add_action(bpy.types.Operator):
    bl_idname = "sprite_baker.add_action"
    bl_label = "添加动作"
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
    bl_label = "删除动作"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        item = get_active_item(context.scene.sprite_baker_settings)
        if item and item.actions:
            item.actions.remove(item.active_action_index)
            item.active_action_index = max(0, item.active_action_index - 1)
        return {"FINISHED"}


class SBK_OT_generate_directions(bpy.types.Operator):
    bl_idname = "sprite_baker.generate_directions"
    bl_label = "生成方向"
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
    bl_label = "删除方向"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        item = get_active_item(context.scene.sprite_baker_settings)
        if item and item.directions:
            item.directions.remove(item.active_direction_index)
            item.active_direction_index = max(0, item.active_direction_index - 1)
        return {"FINISHED"}


class SBK_OT_create_bake_camera(bpy.types.Operator):
    bl_idname = "sprite_baker.create_bake_camera"
    bl_label = "创建/更新烘焙相机"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        settings = context.scene.sprite_baker_settings
        item = get_active_item(settings)
        if item is not None:
            objects = target_objects(item)
        else:
            objects = [obj for obj in context.scene.objects if obj.type == "MESH" and not obj.hide_render]
        if not objects:
            self.report({"WARNING"}, "没有可用于构图的网格物体。")
            return {"CANCELLED"}

        apply_pixel_canvas_preset(settings)
        camera = make_visible_bake_camera(context.scene, settings)
        configure_camera(context.scene, camera, settings, object_bounds(objects), 0.0)
        attach_bake_camera_grid(camera, settings)
        settings.camera_source = "VISIBLE_BAKE_CAMERA"
        settings.bake_camera = camera
        camera.select_set(True)
        context.view_layer.objects.active = camera
        self.report({"INFO"}, f"烘焙相机已更新：{camera.name}")
        return {"FINISHED"}


class SBK_OT_refresh_pixel_grid(bpy.types.Operator):
    bl_idname = "sprite_baker.refresh_pixel_grid"
    bl_label = "刷新像素栅格"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        settings = context.scene.sprite_baker_settings
        apply_pixel_canvas_preset(settings)
        camera = settings.bake_camera or context.scene.camera
        if camera is None or camera.type != "CAMERA":
            self.report({"WARNING"}, "请先创建或指定烘焙相机。")
            return {"CANCELLED"}
        attach_bake_camera_grid(camera, settings)
        self.report({"INFO"}, f"像素栅格已刷新：{settings.resolution_x} x {settings.resolution_y}")
        return {"FINISHED"}


class SBK_OT_clear_pixel_grid(bpy.types.Operator):
    bl_idname = "sprite_baker.clear_pixel_grid"
    bl_label = "清理像素栅格"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        cleared = clear_grid_backgrounds()
        self.report({"INFO"}, f"已清理 {cleared} 个像素栅格背景。")
        return {"FINISHED"}


class SBK_OT_validate(bpy.types.Operator):
    bl_idname = "sprite_baker.validate"
    bl_label = "检查烘焙配置"
    bl_options = {"REGISTER"}

    def execute(self, context):
        errors = validate_settings(context)
        if errors:
            for error in errors:
                self.report({"ERROR"}, error)
            return {"CANCELLED"}
        self.report({"INFO"}, "烘焙配置检查通过。")
        return {"FINISHED"}


class SBK_OT_preview(bpy.types.Operator):
    bl_idname = "sprite_baker.preview"
    bl_label = "预览当前帧"
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
            self.report({"ERROR"}, f"预览失败：{exc}")
            return {"CANCELLED"}
        self.report({"INFO"}, f"预览已写入：{', '.join(files)}")
        return {"FINISHED"}


class SBK_OT_export(bpy.types.Operator):
    bl_idname = "sprite_baker.export"
    bl_label = "导出精灵序列"
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
            self.report({"ERROR"}, f"导出失败：{exc}")
            return {"CANCELLED"}
        self.report({"INFO"}, f"已导出 {count} 个通道帧文件。")
        return {"FINISHED"}


def apply_pixel_canvas_preset(settings):
    if not settings.enable_pixel_bake or settings.pixel_canvas_preset == "CUSTOM":
        return
    size = int(settings.pixel_canvas_preset)
    settings.resolution_x = size
    settings.resolution_y = size
    settings.pixel_preview_scale = 1.0


def attach_bake_camera_grid(camera, settings):
    attach_grid_background(
        camera.data,
        max(1, settings.resolution_x),
        max(1, settings.resolution_y),
        settings.pixel_grid_opacity,
    )
    camera.data.update_tag()


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
