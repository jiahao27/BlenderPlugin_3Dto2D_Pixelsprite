import bpy


def object_mask_poll(self, obj):
    return obj is None or obj.type in {"MESH", "EMPTY", "ARMATURE"}


def armature_poll(self, obj):
    return obj is None or obj.type == "ARMATURE"


def camera_poll(self, obj):
    return obj is None or obj.type == "CAMERA"


def update_pixel_preview_settings(self, context):
    if context is None:
        return
    from .pixel_tools.viewport_preview import set_viewport_pixel_transform

    set_viewport_pixel_transform(
        context.scene,
        self.pixel_preview_scale,
        self.pixel_preview_offset_x,
        self.pixel_preview_offset_y,
    )


def update_pixel_canvas_preset(self, context):
    if context is None or self.pixel_canvas_preset == "CUSTOM":
        return

    size = int(self.pixel_canvas_preset)
    self.resolution_x = size
    self.resolution_y = size
    self.pixel_preview_scale = 1.0

    scene = context.scene
    camera = self.bake_camera or scene.camera
    if camera is not None and camera.type == "CAMERA":
        from .pixel_tools.grid_images import attach_grid_background

        attach_grid_background(camera.data, size, size, self.pixel_grid_opacity)
        camera.data.update_tag()


def update_pixel_grid_opacity(self, context):
    if context is None:
        return

    scene = context.scene
    camera = self.bake_camera or scene.camera
    if camera is None or camera.type != "CAMERA":
        return

    from .pixel_tools.grid_images import attach_grid_background

    attach_grid_background(camera.data, max(1, self.resolution_x), max(1, self.resolution_y), self.pixel_grid_opacity)
    camera.data.update_tag()


def update_enable_pixel_bake(self, context):
    if not self.enable_pixel_bake:
        return
    update_pixel_canvas_preset(self, context)


class SBK_MaskAssignment(bpy.types.PropertyGroup):
    enabled: bpy.props.BoolProperty(name="启用遮罩", description="为 MaskTex 通道使用这些 RGBA 权重", default=False)
    r: bpy.props.FloatProperty(name="红", default=0.0, min=0.0, max=1.0)
    g: bpy.props.FloatProperty(name="绿", default=0.0, min=0.0, max=1.0)
    b: bpy.props.FloatProperty(name="蓝", default=0.0, min=0.0, max=1.0)
    a: bpy.props.FloatProperty(name="透明", default=1.0, min=0.0, max=1.0)


class SBK_ActionSlot(bpy.types.PropertyGroup):
    action: bpy.props.PointerProperty(name="动作", type=bpy.types.Action)


class SBK_DirectionSlot(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(name="方向名", default="dir_000")
    angle: bpy.props.FloatProperty(name="角度", description="方向角度（度）", default=0.0)


class SBK_ExportItem(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(name="名称", default="Sprite")
    target_type: bpy.props.EnumProperty(
        name="目标类型",
        items=(
            ("OBJECT", "物体", "烘焙一个物体"),
            ("COLLECTION", "集合", "烘焙集合中的网格物体"),
        ),
        default="OBJECT",
    )
    target_object: bpy.props.PointerProperty(name="物体", type=bpy.types.Object, poll=object_mask_poll)
    target_collection: bpy.props.PointerProperty(name="集合", type=bpy.types.Collection)
    armature: bpy.props.PointerProperty(name="骨架", type=bpy.types.Object, poll=armature_poll)
    animation_mode: bpy.props.EnumProperty(
        name="动画模式",
        items=(
            ("STATIC", "静态", "按帧范围烘焙当前场景状态"),
            ("ACTIONS", "动作", "按 Action 列表批量烘焙"),
        ),
        default="STATIC",
    )
    actions: bpy.props.CollectionProperty(type=SBK_ActionSlot)
    active_action_index: bpy.props.IntProperty(default=0, min=0)
    direction_preset: bpy.props.EnumProperty(
        name="方向",
        items=(
            ("SINGLE", "单方向", "仅 0 度"),
            ("FOUR", "4 向", "0、90、180、270 度"),
            ("EIGHT", "8 向", "八个均匀方向"),
            ("CUSTOM", "自定义", "用逗号分隔角度"),
        ),
        default="SINGLE",
    )
    custom_directions: bpy.props.StringProperty(name="自定义角度", description="例如 0,45,90", default="0")
    directions: bpy.props.CollectionProperty(type=SBK_DirectionSlot)
    active_direction_index: bpy.props.IntProperty(default=0, min=0)
    frame_start: bpy.props.IntProperty(name="起始帧", default=1, min=0)
    frame_end: bpy.props.IntProperty(name="结束帧", default=1, min=0)
    use_action_frame_range: bpy.props.BoolProperty(name="使用动作帧范围", default=True)
    pivot_mode: bpy.props.EnumProperty(
        name="支点",
        items=(
            ("AUTO", "自动边界", "使用目标边界中心"),
            ("ORIGIN", "物体原点", "使用目标物体原点"),
            ("CURSOR", "3D 游标", "使用场景游标"),
            ("CUSTOM", "自定义", "使用自定义世界坐标"),
        ),
        default="AUTO",
    )
    custom_pivot: bpy.props.FloatVectorProperty(name="自定义支点", size=3, subtype="XYZ", default=(0.0, 0.0, 0.0))


class SBK_Settings(bpy.types.PropertyGroup):
    bake_mode: bpy.props.EnumProperty(
        name="烘焙模式",
        items=(
            ("CAMERA", "相机烘焙", "摄像机看到什么就烘焙什么"),
            ("BATCH", "批量动作烘焙", "按目标、动作、方向批量烘焙"),
        ),
        default="CAMERA",
    )
    resolution_x: bpy.props.IntProperty(name="宽度", default=128, min=1, max=8192)
    resolution_y: bpy.props.IntProperty(name="高度", default=128, min=1, max=8192)
    pixels_per_unit: bpy.props.FloatProperty(name="每单位像素", default=100.0, min=0.01)
    output_dir: bpy.props.StringProperty(name="输出目录", subtype="DIR_PATH", default="//sprite_bake")
    naming_template: bpy.props.StringProperty(name="命名模板", default="{item}_{action}_{direction}_{frame}_{pass}")
    merge_atlas: bpy.props.BoolProperty(
        name="合并为大图",
        description="导出序列帧后，按通道和方向生成对应 Sprite Sheet；质数帧数会跳过合并并给出提醒",
        default=False,
    )
    camera_mode: bpy.props.EnumProperty(
        name="相机模式",
        items=(
            ("ORTHO", "正交", "正交相机"),
            ("WEAK_PERSPECTIVE", "弱透视", "长焦透视相机"),
        ),
        default="ORTHO",
    )
    camera_source: bpy.props.EnumProperty(
        name="相机来源",
        items=(
            ("VISIBLE_BAKE_CAMERA", "可见烘焙相机", "使用场景中可见、可调整的烘焙相机"),
            ("TEMP_AUTO_CAMERA", "临时自动相机", "批量动作烘焙时自动创建临时相机"),
        ),
        default="VISIBLE_BAKE_CAMERA",
    )
    bake_camera: bpy.props.PointerProperty(name="烘焙相机", type=bpy.types.Object, poll=camera_poll)
    camera_animation_target: bpy.props.PointerProperty(
        name="动画对象",
        description="相机烘焙时可选；角色动画通常选择骨架，物体关键帧动画选择物体本身",
        type=bpy.types.Object,
        poll=object_mask_poll,
    )
    camera_action: bpy.props.PointerProperty(
        name="动作",
        description="相机烘焙时可选；留空则使用当前时间轴/对象当前绑定的动作",
        type=bpy.types.Action,
    )
    margin: bpy.props.FloatProperty(name="自动构图边距", default=0.12, min=0.0, max=1.0)
    pixel_canvas_preset: bpy.props.EnumProperty(
        name="像素画布",
        items=(
            ("64", "64 x 64", "更粗颗粒"),
            ("128", "128 x 128", "中等颗粒"),
            ("256", "256 x 256", "更细颗粒"),
            ("CUSTOM", "自定义", "使用手动宽度和高度"),
        ),
        default="128",
        update=update_pixel_canvas_preset,
    )
    frame_start: bpy.props.IntProperty(name="起始帧", default=1, min=0)
    frame_end: bpy.props.IntProperty(name="结束帧", default=1, min=0)
    frame_sampling: bpy.props.EnumProperty(
        name="帧采样",
        items=(
            ("FRAME_COUNT", "按烘焙帧数", "在帧范围内均匀采样指定数量"),
            ("FRAME_STEP", "按帧步长", "按起始帧、结束帧和帧步长导出"),
        ),
        default="FRAME_COUNT",
    )
    bake_frame_count: bpy.props.IntProperty(name="烘焙帧数", default=8, min=1, max=10000)
    frame_step: bpy.props.IntProperty(name="帧步长", default=1, min=1, max=100)
    direction_strategy: bpy.props.EnumProperty(
        name="方向策略",
        items=(
            ("ROTATE_TARGET", "旋转目标", "固定相机并旋转导出物体"),
            ("CAMERA_ORBIT", "环绕相机", "固定物体并让相机环绕"),
        ),
        default="ROTATE_TARGET",
    )
    batch_framing_mode: bpy.props.EnumProperty(
        name="构图方式",
        items=(
            ("LOCK_ACTION", "固定动作窗口", "先扫描整段动作和所有方向，使用最大边界烘焙整组序列"),
            ("PER_FRAME", "逐帧自动构图", "每一帧单独计算相机窗口，可能导致动画大小跳动"),
        ),
        default="LOCK_ACTION",
    )
    enable_pixel_bake: bpy.props.BoolProperty(name="启用像素烘焙", default=False, update=update_enable_pixel_bake)
    pixel_preview_scale: bpy.props.FloatProperty(
        name="像素颗粒度",
        description="先缩小再放大的比例；越小颗粒越粗，越接近 1 越接近原图",
        default=0.5,
        min=0.001,
        max=1.0,
        subtype="FACTOR",
        update=update_pixel_preview_settings,
    )
    pixel_preview_offset_x: bpy.props.FloatProperty(
        name="像素偏移 X",
        default=0.0,
        soft_min=-32.0,
        soft_max=32.0,
        update=update_pixel_preview_settings,
    )
    pixel_preview_offset_y: bpy.props.FloatProperty(
        name="像素偏移 Y",
        default=0.0,
        soft_min=-32.0,
        soft_max=32.0,
        update=update_pixel_preview_settings,
    )
    pixel_grid_opacity: bpy.props.FloatProperty(
        name="栅格透明度",
        default=0.35,
        min=0.0,
        max=1.0,
        subtype="FACTOR",
        update=update_pixel_grid_opacity,
    )
    use_albedo: bpy.props.BoolProperty(name="Albedo", default=True)
    use_normal: bpy.props.BoolProperty(name="NormalMap", default=True)
    unity_2d_normal_map: bpy.props.BoolProperty(
        name="按 Unity 2D 法线坐标导出",
        description="将相机前方转换为 Unity Sprite 法线贴图的 +Z 方向",
        default=False,
    )
    normal_map_edge_padding: bpy.props.BoolProperty(
        name="NormalMap 透明边缘向外扩 1 像素",
        description="复制轮廓相邻法线的 RGB 到外侧透明像素，降低 Unity 双线性采样造成的边缘异常",
        default=False,
    )
    use_mask: bpy.props.BoolProperty(name="MaskTex", default=True)
    unity_names: bpy.props.BoolProperty(name="Unity 命名", default=True)
    export_items: bpy.props.CollectionProperty(type=SBK_ExportItem)
    active_export_item_index: bpy.props.IntProperty(default=0, min=0)


def register_properties():
    bpy.types.Scene.sprite_baker_settings = bpy.props.PointerProperty(type=SBK_Settings)
    bpy.types.Object.sprite_baker_mask = bpy.props.PointerProperty(type=SBK_MaskAssignment)
    bpy.types.Material.sprite_baker_mask = bpy.props.PointerProperty(type=SBK_MaskAssignment)


def unregister_properties():
    del bpy.types.Material.sprite_baker_mask
    del bpy.types.Object.sprite_baker_mask
    del bpy.types.Scene.sprite_baker_settings
