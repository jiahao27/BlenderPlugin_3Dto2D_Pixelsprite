import bpy


def object_mask_poll(self, obj):
    return obj is None or obj.type in {"MESH", "EMPTY", "ARMATURE"}


def armature_poll(self, obj):
    return obj is None or obj.type == "ARMATURE"


class SBK_MaskAssignment(bpy.types.PropertyGroup):
    enabled: bpy.props.BoolProperty(
        name="启用遮罩",
        description="为 MaskTex 通道使用这些 RGBA 权重",
        default=False,
    )
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
        name="导出目标类型",
        items=(
            ("OBJECT", "物体", "导出一个物体"),
            ("COLLECTION", "集合", "导出集合中的可渲染网格物体"),
        ),
        default="OBJECT",
    )
    target_object: bpy.props.PointerProperty(name="物体", type=bpy.types.Object, poll=object_mask_poll)
    target_collection: bpy.props.PointerProperty(name="集合", type=bpy.types.Collection)
    armature: bpy.props.PointerProperty(name="骨架", type=bpy.types.Object, poll=armature_poll)
    animation_mode: bpy.props.EnumProperty(
        name="动画模式",
        items=(
            ("STATIC", "静态", "将当前帧导出为静态精灵"),
            ("ACTIONS", "动作", "导出列表中的每个动作"),
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
            ("EIGHT", "8 向", "八个均匀分布方向"),
            ("CUSTOM", "自定义", "用逗号分隔自定义角度"),
        ),
        default="SINGLE",
    )
    custom_directions: bpy.props.StringProperty(
        name="自定义角度",
        description="逗号分隔的角度，例如：0,45,90",
        default="0",
    )
    directions: bpy.props.CollectionProperty(type=SBK_DirectionSlot)
    active_direction_index: bpy.props.IntProperty(default=0, min=0)
    frame_start: bpy.props.IntProperty(name="起始帧", default=1, min=0)
    frame_end: bpy.props.IntProperty(name="结束帧", default=1, min=0)
    use_action_frame_range: bpy.props.BoolProperty(
        name="使用动作帧范围",
        description="使用所选动作的帧范围，而不是项目自定义范围",
        default=True,
    )
    pivot_mode: bpy.props.EnumProperty(
        name="支点",
        items=(
            ("AUTO", "自动边界", "使用计算边界中心"),
            ("ORIGIN", "物体原点", "使用目标物体原点"),
            ("CURSOR", "3D 游标", "使用场景游标"),
            ("CUSTOM", "自定义", "使用自定义世界坐标支点"),
        ),
        default="AUTO",
    )
    custom_pivot: bpy.props.FloatVectorProperty(name="自定义支点", size=3, subtype="XYZ", default=(0.0, 0.0, 0.0))


class SBK_Settings(bpy.types.PropertyGroup):
    resolution_x: bpy.props.IntProperty(name="宽度", default=128, min=1, max=8192)
    resolution_y: bpy.props.IntProperty(name="高度", default=128, min=1, max=8192)
    pixels_per_unit: bpy.props.FloatProperty(name="每单位像素", default=100.0, min=0.01)
    output_dir: bpy.props.StringProperty(name="输出目录", subtype="DIR_PATH", default="//sprite_bake")
    naming_template: bpy.props.StringProperty(
        name="命名模板",
        default="{item}_{action}_{direction}_{frame}_{pass}",
    )
    camera_mode: bpy.props.EnumProperty(
        name="相机模式",
        items=(
            ("ORTHO", "正交", "正交精灵相机"),
            ("WEAK_PERSPECTIVE", "弱透视", "长焦透视相机"),
        ),
        default="ORTHO",
    )
    margin: bpy.props.FloatProperty(name="边距", description="构图边距比例", default=0.12, min=0.0, max=1.0)
    frame_step: bpy.props.IntProperty(name="帧步长", default=1, min=1, max=100)
    direction_strategy: bpy.props.EnumProperty(
        name="方向策略",
        items=(
            ("ROTATE_TARGET", "旋转目标", "固定相机并旋转导出物体"),
            ("CAMERA_ORBIT", "环绕相机", "固定物体并让临时相机环绕"),
        ),
        default="ROTATE_TARGET",
    )
    use_albedo: bpy.props.BoolProperty(name="Albedo", default=True)
    use_normal: bpy.props.BoolProperty(name="NormalMap", default=True)
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
