import bpy


DEFAULT_RESOLUTION = 64


def apply_resolution_preset(self, context):
    if context is None or self.resolution_preset == "CUSTOM":
        return
    scene = context.scene
    size = int(self.resolution_preset)
    scene.render.resolution_x = size
    scene.render.resolution_y = size
    self.current_resolution_x = size
    self.current_resolution_y = size
    self.custom_resolution_x = size
    self.custom_resolution_y = size


def apply_custom_resolution(self, context):
    if context is None or self.resolution_preset != "CUSTOM":
        return
    scene = context.scene
    width = max(1, self.custom_resolution_x)
    height = max(1, self.custom_resolution_y)
    scene.render.resolution_x = width
    scene.render.resolution_y = height
    self.current_resolution_x = width
    self.current_resolution_y = height


def update_grid_opacity(self, context):
    from .grid_images import set_grid_background_opacity

    if context is None:
        return
    set_grid_background_opacity(self.grid_opacity)


def update_viewport_preview_scale(self, context):
    from .viewport_preview import set_viewport_pixel_transform
    if context is None:
        return
    set_viewport_pixel_transform(context.scene, self.viewport_preview_scale, self.viewport_preview_offset_x, self.viewport_preview_offset_y)


def update_viewport_preview_offset(self, context):
    from .viewport_preview import set_viewport_pixel_transform
    if context is None:
        return
    set_viewport_pixel_transform(context.scene, self.viewport_preview_scale, self.viewport_preview_offset_x, self.viewport_preview_offset_y)


def update_outline_settings(self, context):
    from .outline_utils import apply_outline_settings_to_tree
    from .viewport_preview import get_scene_compositor_tree

    if context is None:
        return
    node_tree = get_scene_compositor_tree(context.scene)
    if node_tree is None:
        return
    apply_outline_settings_to_tree(node_tree, self.outline_thickness, self.outline_color, self.outline_background_color, self.viewport_preview_scale)


def _get_active_camera(context):
    if context is None:
        return None
    active_object = context.view_layer.objects.active
    if active_object is None or active_object.type != "CAMERA":
        return None
    return active_object


def update_selected_camera_distance(self, context):
    from .camera_utils import get_camera_type
    camera_object = _get_active_camera(context)
    if camera_object is None:
        return
    camera_type = get_camera_type(self, camera_object)
    if camera_type == "ISO":
        delta = self.iso_camera_distance - self.last_camera_distance
        camera_object.location.x += delta
        camera_object.location.y -= delta
        camera_object.location.z += delta
    else:
        camera_object.location.y = -self.iso_camera_distance
    self.last_camera_distance = self.iso_camera_distance


def update_selected_camera_ortho_scale(self, context):
    camera_object = _get_active_camera(context)
    if camera_object is None or camera_object.data.type != "ORTHO":
        return
    camera_object.data.ortho_scale = self.camera_ortho_scale


class SBK_PixelToolsSettings(bpy.types.PropertyGroup):
    status_message: bpy.props.StringProperty(name="状态消息", default="像素工具已就绪。")
    resolution_preset: bpy.props.EnumProperty(
        name="分辨率",
        items=(
            ("16", "16 像素", "16 x 16"),
            ("32", "32 像素", "32 x 32"),
            ("64", "64 像素", "64 x 64"),
            ("128", "128 像素", "128 x 128"),
            ("256", "256 像素", "256 x 256"),
            ("CUSTOM", "自定义", "自定义分辨率"),
        ),
        default=str(DEFAULT_RESOLUTION),
        update=apply_resolution_preset,
    )
    custom_resolution_x: bpy.props.IntProperty(name="自定义宽度", default=DEFAULT_RESOLUTION, min=1, update=apply_custom_resolution)
    custom_resolution_y: bpy.props.IntProperty(name="自定义高度", default=DEFAULT_RESOLUTION, min=1, update=apply_custom_resolution)
    current_resolution_x: bpy.props.IntProperty(name="当前宽度", default=DEFAULT_RESOLUTION)
    current_resolution_y: bpy.props.IntProperty(name="当前高度", default=DEFAULT_RESOLUTION)
    camera_projection: bpy.props.EnumProperty(
        name="投影",
        items=(("ORTHO", "正交", "正交相机"), ("PERSP", "透视", "透视相机")),
        default="ORTHO",
    )
    pixel_camera_type: bpy.props.EnumProperty(
        name="相机类型",
        items=(("PIXEL", "正面相机", "前向像素相机"), ("ISO", "等距相机", "等距像素相机")),
        default="PIXEL",
    )
    iso_camera_distance: bpy.props.FloatProperty(name="相机距离", default=12.0, min=0.001, unit="LENGTH", update=update_selected_camera_distance)
    camera_ortho_scale: bpy.props.FloatProperty(name="正交缩放", default=5.0, min=0.001, update=update_selected_camera_ortho_scale)
    last_camera_distance: bpy.props.FloatProperty(name="上次距离", default=12.0, options={"HIDDEN"})
    grid_opacity: bpy.props.FloatProperty(name="网格透明度", default=0.35, min=0.0, max=1.0, subtype="FACTOR", update=update_grid_opacity)
    viewport_preview_scale: bpy.props.FloatProperty(name="预览缩放", default=0.25, min=0.001, max=1.0, subtype="FACTOR", update=update_viewport_preview_scale)
    viewport_preview_offset_x: bpy.props.FloatProperty(name="预览偏移 X", default=0.0, soft_min=-32.0, soft_max=32.0, update=update_viewport_preview_offset)
    viewport_preview_offset_y: bpy.props.FloatProperty(name="预览偏移 Y", default=0.0, soft_min=-32.0, soft_max=32.0, update=update_viewport_preview_offset)
    outline_thickness: bpy.props.IntProperty(name="描边粗细", default=2, min=0, max=128, update=update_outline_settings)
    outline_color: bpy.props.FloatVectorProperty(name="描边颜色", subtype="COLOR", size=4, min=0.0, max=1.0, default=(0.0, 0.0, 0.0, 1.0), update=update_outline_settings)
    outline_background_color: bpy.props.FloatVectorProperty(name="背景颜色", subtype="COLOR", size=4, min=0.0, max=1.0, default=(0.0, 0.0, 0.0, 0.0), update=update_outline_settings)
    material_type: bpy.props.EnumProperty(
        name="材质类型",
        items=(
            ("FLAT", "平面色", "创建平面色材质"),
            ("FLAT_UV", "平面 UV", "创建调色板 UV 材质"),
            ("TOON", "Toon", "创建卡通材质"),
            ("IMAGE_PIXEL", "图片像素化", "创建图片像素化材质"),
        ),
        default="FLAT",
    )
    material_assignment_mode: bpy.props.EnumProperty(
        name="赋值方式",
        items=(("ADD_SLOT", "新增槽位", "新增材质槽"), ("REPLACE_ACTIVE", "替换活动槽位", "替换活动材质槽")),
        default="ADD_SLOT",
    )


CLASSES = (SBK_PixelToolsSettings,)


def register_properties():
    bpy.types.Scene.sprite_baker_pixel_tools = bpy.props.PointerProperty(type=SBK_PixelToolsSettings)


def unregister_properties():
    del bpy.types.Scene.sprite_baker_pixel_tools
