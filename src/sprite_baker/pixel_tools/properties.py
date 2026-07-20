import bpy


DEFAULT_RESOLUTION = 64


def apply_resolution_preset(self, context):
    if context is None or self.resolution_preset == "CUSTOM":
        return
    size = int(self.resolution_preset)
    context.scene.render.resolution_x = size
    context.scene.render.resolution_y = size
    self.current_resolution_x = size
    self.current_resolution_y = size
    self.custom_resolution_x = size
    self.custom_resolution_y = size


def apply_custom_resolution(self, context):
    if context is None or self.resolution_preset != "CUSTOM":
        return
    width = max(1, self.custom_resolution_x)
    height = max(1, self.custom_resolution_y)
    context.scene.render.resolution_x = width
    context.scene.render.resolution_y = height
    self.current_resolution_x = width
    self.current_resolution_y = height


class SBK_PixelToolsSettings(bpy.types.PropertyGroup):
    status_message: bpy.props.StringProperty(name="状态消息", default="像素材质工具已就绪。")
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
    grid_opacity: bpy.props.FloatProperty(name="网格透明度", default=0.35, min=0.0, max=1.0, subtype="FACTOR")
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
        items=(
            ("ADD_SLOT", "新增槽位", "新增材质槽"),
            ("REPLACE_ACTIVE", "替换活动槽位", "替换活动材质槽"),
        ),
        default="ADD_SLOT",
    )


CLASSES = (SBK_PixelToolsSettings,)


def register_properties():
    bpy.types.Scene.sprite_baker_pixel_tools = bpy.props.PointerProperty(type=SBK_PixelToolsSettings)


def unregister_properties():
    del bpy.types.Scene.sprite_baker_pixel_tools
