import bpy

from .camera_utils import apply_camera_projection, apply_camera_transform
from .grid_images import attach_grid_background, clear_grid_backgrounds
from .materials import SBK_OT_create_pixel_material
from .outline_utils import apply_outline_settings_to_tree, setup_outline_nodes
from .status import set_status
from .viewport_display import set_render_preview_pixel_size, set_viewport_render_preview
from .viewport_preview import (
    VIEWPORT_PIXEL_GROUP_NAME,
    VIEWPORT_PIXEL_GROUP_NODE_NAME,
    VIEWPORT_PIXEL_DOWNSCALE_NODE_NAME,
    VIEWPORT_PIXEL_UPSCALE_NODE_NAME,
    VIEWPORT_PIXEL_VALUE_NODE_NAME,
    VIEWPORT_PIXEL_VIEWER_NODE_NAME,
    get_scene_compositor_tree,
    setup_viewport_pixel_preview,
    set_viewport_pixel_transform,
)


def _get_scene_resolution(context):
    settings = context.scene.sprite_baker_pixel_tools
    return max(1, settings.current_resolution_x), max(1, settings.current_resolution_y)


def _resolution_label(width, height):
    return f"{width}x{height}"


def _create_camera(base_name):
    camera_data = bpy.data.cameras.new(base_name)
    camera_object = bpy.data.objects.new(base_name, camera_data)
    bpy.context.collection.objects.link(camera_object)
    return camera_object


def _get_active_camera(context):
    active_object = context.view_layer.objects.active
    if active_object is None or active_object.type != "CAMERA":
        return None
    return active_object


def _finish_camera_setup(context, camera_object, width, height):
    settings = context.scene.sprite_baker_pixel_tools
    attach_grid_background(camera_object.data, width, height, settings.grid_opacity)
    context.scene.camera = camera_object
    camera_object.select_set(True)
    context.view_layer.objects.active = camera_object


def _create_front_camera(context):
    settings = context.scene.sprite_baker_pixel_tools
    width, height = _get_scene_resolution(context)
    label = _resolution_label(width, height)
    camera_object = _create_camera(f"SBK 正面 {label} 相机")
    apply_camera_transform(camera_object, "PIXEL", settings.iso_camera_distance)
    apply_camera_projection(camera_object, settings.camera_projection, settings.camera_ortho_scale)
    _finish_camera_setup(context, camera_object, width, height)
    return label, camera_object.name


def _create_iso_camera(context):
    settings = context.scene.sprite_baker_pixel_tools
    width, height = _get_scene_resolution(context)
    label = _resolution_label(width, height)
    camera_object = _create_camera(f"SBK 等距 {label} 相机")
    apply_camera_transform(camera_object, "ISO", settings.iso_camera_distance)
    apply_camera_projection(camera_object, settings.camera_projection, settings.camera_ortho_scale)
    _finish_camera_setup(context, camera_object, width, height)
    return label, camera_object.name


class SBK_OT_apply_render_settings(bpy.types.Operator):
    bl_idname = "sprite_baker.apply_render_settings"
    bl_label = "应用像素渲染设置"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        settings = context.scene.sprite_baker_pixel_tools
        scene = context.scene
        try:
            scene.render.engine = "BLENDER_EEVEE_NEXT"
        except TypeError:
            scene.render.engine = "BLENDER_EEVEE"
        scene.render.filter_size = 0.0
        scene.render.resolution_percentage = 100
        scene.view_settings.view_transform = "Standard"
        if settings.resolution_preset == "CUSTOM":
            width = max(1, settings.custom_resolution_x)
            height = max(1, settings.custom_resolution_y)
        else:
            width = int(settings.resolution_preset)
            height = width
            settings.custom_resolution_x = width
            settings.custom_resolution_y = height
        scene.render.resolution_x = width
        scene.render.resolution_y = height
        settings.current_resolution_x = width
        settings.current_resolution_y = height
        set_render_preview_pixel_size(scene)
        set_viewport_render_preview(context)
        set_status(context, "像素渲染设置已应用。")
        return {"FINISHED"}


class SBK_OT_set_camera_projection(bpy.types.Operator):
    bl_idname = "sprite_baker.set_camera_projection"
    bl_label = "设置相机投影"
    bl_options = {"REGISTER", "UNDO"}
    projection: bpy.props.EnumProperty(items=(("ORTHO", "正交", ""), ("PERSP", "透视", "")), default="ORTHO")
    def execute(self, context):
        context.scene.sprite_baker_pixel_tools.camera_projection = self.projection
        return {"FINISHED"}


class SBK_OT_create_selected_pixel_camera(bpy.types.Operator):
    bl_idname = "sprite_baker.create_selected_pixel_camera"
    bl_label = "创建相机"
    bl_options = {"REGISTER", "UNDO"}
    def execute(self, context):
        settings = context.scene.sprite_baker_pixel_tools
        if settings.pixel_camera_type == "ISO":
            _create_iso_camera(context)
        else:
            _create_front_camera(context)
        return {"FINISHED"}


class SBK_OT_update_selected_pixel_camera(bpy.types.Operator):
    bl_idname = "sprite_baker.update_selected_pixel_camera"
    bl_label = "更新选中相机"
    bl_options = {"REGISTER", "UNDO"}
    def execute(self, context):
        camera_object = _get_active_camera(context)
        if camera_object is None:
            self.report({"WARNING"}, "请先选中一个相机。")
            return {"CANCELLED"}
        settings = context.scene.sprite_baker_pixel_tools
        width, height = _get_scene_resolution(context)
        label = _resolution_label(width, height)
        apply_camera_projection(camera_object, settings.camera_projection, settings.camera_ortho_scale)
        attach_grid_background(camera_object.data, width, height, settings.grid_opacity)
        context.scene.camera = camera_object
        set_status(context, "相机已更新。")
        return {"FINISHED"}


class SBK_OT_create_front_pixel_camera(bpy.types.Operator):
    bl_idname = "sprite_baker.create_front_pixel_camera"
    bl_label = "创建正面相机"
    bl_options = {"REGISTER", "UNDO"}
    def execute(self, context):
        _create_front_camera(context)
        return {"FINISHED"}


class SBK_OT_create_iso_pixel_camera(bpy.types.Operator):
    bl_idname = "sprite_baker.create_iso_pixel_camera"
    bl_label = "创建等距相机"
    bl_options = {"REGISTER", "UNDO"}
    def execute(self, context):
        _create_iso_camera(context)
        return {"FINISHED"}


class SBK_OT_cleanup_grid_images(bpy.types.Operator):
    bl_idname = "sprite_baker.cleanup_grid_images"
    bl_label = "清理网格背景"
    bl_options = {"REGISTER", "UNDO"}
    def execute(self, context):
        clear_grid_backgrounds()
        return {"FINISHED"}


class SBK_OT_setup_viewport_pixel_preview(bpy.types.Operator):
    bl_idname = "sprite_baker.setup_viewport_pixel_preview"
    bl_label = "设置视口预览"
    bl_options = {"REGISTER", "UNDO"}
    def execute(self, context):
        settings = context.scene.sprite_baker_pixel_tools
        set_viewport_render_preview(context, rendered=True)
        try:
            setup_viewport_pixel_preview(
                context.scene,
                settings.viewport_preview_scale,
                settings.viewport_preview_offset_x,
                settings.viewport_preview_offset_y,
            )
        except RuntimeError as error:
            self.report({"WARNING"}, str(error))
            return {"CANCELLED"}
        set_viewport_pixel_transform(
            context.scene,
            settings.viewport_preview_scale,
            settings.viewport_preview_offset_x,
            settings.viewport_preview_offset_y,
        )
        return {"FINISHED"}


class SBK_OT_update_viewport_preview_resolution(bpy.types.Operator):
    bl_idname = "sprite_baker.update_viewport_preview_resolution"
    bl_label = "更新预览缩放"
    bl_options = {"REGISTER", "UNDO"}
    def execute(self, context):
        settings = context.scene.sprite_baker_pixel_tools
        set_viewport_render_preview(context, rendered=True)
        set_viewport_pixel_transform(
            context.scene,
            settings.viewport_preview_scale,
            settings.viewport_preview_offset_x,
            settings.viewport_preview_offset_y,
        )
        return {"FINISHED"}


class SBK_OT_remove_viewport_pixel_preview(bpy.types.Operator):
    bl_idname = "sprite_baker.remove_viewport_pixel_preview"
    bl_label = "移除视口预览"
    bl_options = {"REGISTER", "UNDO"}
    def execute(self, context):
        node_tree = get_scene_compositor_tree(context.scene)
        if node_tree is None:
            return {"FINISHED"}
        for name in (VIEWPORT_PIXEL_GROUP_NODE_NAME, VIEWPORT_PIXEL_VIEWER_NODE_NAME):
            node = node_tree.nodes.get(name)
            if node is not None:
                node_tree.nodes.remove(node)
        group = bpy.data.node_groups.get(VIEWPORT_PIXEL_GROUP_NAME)
        if group is not None and group.users == 0:
            bpy.data.node_groups.remove(group)
        return {"FINISHED"}


class SBK_OT_toggle_viewport_display(bpy.types.Operator):
    bl_idname = "sprite_baker.toggle_viewport_display"
    bl_label = "切换视口辅助线"
    bl_options = {"REGISTER", "UNDO"}
    def execute(self, context):
        space = context.space_data
        if space is None or space.type != "VIEW_3D":
            self.report({"WARNING"}, "请在 3D 视图中使用。")
            return {"CANCELLED"}
        overlay = space.overlay
        props = ("show_floor", "show_ortho_grid", "show_axis_x", "show_axis_y", "show_axis_z")
        should_show = not any(getattr(overlay, prop) for prop in props if hasattr(overlay, prop))
        for prop in props:
            if hasattr(overlay, prop):
                setattr(overlay, prop, should_show)
        return {"FINISHED"}


class SBK_OT_setup_outline(bpy.types.Operator):
    bl_idname = "sprite_baker.setup_outline"
    bl_label = "设置描边"
    bl_options = {"REGISTER", "UNDO"}
    def execute(self, context):
        settings = context.scene.sprite_baker_pixel_tools
        try:
            setup_outline_nodes(
                context.scene,
                settings.outline_thickness,
                settings.outline_color,
                settings.outline_background_color,
                settings.viewport_preview_scale,
            )
        except RuntimeError as error:
            self.report({"WARNING"}, str(error))
            return {"CANCELLED"}
        return {"FINISHED"}


class SBK_OT_remove_outline(bpy.types.Operator):
    bl_idname = "sprite_baker.remove_outline"
    bl_label = "移除描边"
    bl_options = {"REGISTER", "UNDO"}
    def execute(self, context):
        from .outline_utils import OUTLINE_NODE_NAMES
        node_tree = get_scene_compositor_tree(context.scene)
        if node_tree is None:
            return {"FINISHED"}
        for node_name in OUTLINE_NODE_NAMES:
            node = node_tree.nodes.get(node_name)
            if node is not None:
                node_tree.nodes.remove(node)
        group = bpy.data.node_groups.get("SBK 描边")
        if group is not None and group.users == 0:
            bpy.data.node_groups.remove(group)
        return {"FINISHED"}


CLASSES = (
    SBK_OT_apply_render_settings,
    SBK_OT_set_camera_projection,
    SBK_OT_create_selected_pixel_camera,
    SBK_OT_update_selected_pixel_camera,
    SBK_OT_create_front_pixel_camera,
    SBK_OT_create_iso_pixel_camera,
    SBK_OT_cleanup_grid_images,
    SBK_OT_setup_viewport_pixel_preview,
    SBK_OT_update_viewport_preview_resolution,
    SBK_OT_remove_viewport_pixel_preview,
    SBK_OT_toggle_viewport_display,
    SBK_OT_setup_outline,
    SBK_OT_remove_outline,
    SBK_OT_create_pixel_material,
)
