import bpy


def object_mask_poll(self, obj):
    return obj is None or obj.type in {"MESH", "EMPTY", "ARMATURE"}


def armature_poll(self, obj):
    return obj is None or obj.type == "ARMATURE"


class SBK_MaskAssignment(bpy.types.PropertyGroup):
    enabled: bpy.props.BoolProperty(
        name="Use Mask",
        description="Use these RGBA weights for the MaskTex pass",
        default=False,
    )
    r: bpy.props.FloatProperty(name="R", default=0.0, min=0.0, max=1.0)
    g: bpy.props.FloatProperty(name="G", default=0.0, min=0.0, max=1.0)
    b: bpy.props.FloatProperty(name="B", default=0.0, min=0.0, max=1.0)
    a: bpy.props.FloatProperty(name="A", default=1.0, min=0.0, max=1.0)


class SBK_ActionSlot(bpy.types.PropertyGroup):
    action: bpy.props.PointerProperty(name="Action", type=bpy.types.Action)


class SBK_DirectionSlot(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(name="Name", default="dir_000")
    angle: bpy.props.FloatProperty(name="Angle", description="Direction angle in degrees", default=0.0)


class SBK_ExportItem(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(name="Name", default="Sprite")
    target_type: bpy.props.EnumProperty(
        name="Target Type",
        items=(
            ("OBJECT", "Object", "Export one object"),
            ("COLLECTION", "Collection", "Export all renderable mesh objects in a collection"),
        ),
        default="OBJECT",
    )
    target_object: bpy.props.PointerProperty(name="Object", type=bpy.types.Object, poll=object_mask_poll)
    target_collection: bpy.props.PointerProperty(name="Collection", type=bpy.types.Collection)
    armature: bpy.props.PointerProperty(name="Armature", type=bpy.types.Object, poll=armature_poll)
    animation_mode: bpy.props.EnumProperty(
        name="Animation",
        items=(
            ("STATIC", "Static", "Export current frame as a static sprite"),
            ("ACTIONS", "Actions", "Export every listed Action"),
        ),
        default="STATIC",
    )
    actions: bpy.props.CollectionProperty(type=SBK_ActionSlot)
    active_action_index: bpy.props.IntProperty(default=0, min=0)
    direction_preset: bpy.props.EnumProperty(
        name="Directions",
        items=(
            ("SINGLE", "Single", "Only 0 degrees"),
            ("FOUR", "4-Way", "0, 90, 180, 270 degrees"),
            ("EIGHT", "8-Way", "Eight evenly spaced directions"),
            ("CUSTOM", "Custom", "Comma separated custom angles"),
        ),
        default="SINGLE",
    )
    custom_directions: bpy.props.StringProperty(
        name="Custom Angles",
        description="Comma separated degrees, for example: 0,45,90",
        default="0",
    )
    directions: bpy.props.CollectionProperty(type=SBK_DirectionSlot)
    active_direction_index: bpy.props.IntProperty(default=0, min=0)
    frame_start: bpy.props.IntProperty(name="Frame Start", default=1, min=0)
    frame_end: bpy.props.IntProperty(name="Frame End", default=1, min=0)
    use_action_frame_range: bpy.props.BoolProperty(
        name="Use Action Range",
        description="Use the selected Action frame range instead of the item frame range",
        default=True,
    )
    pivot_mode: bpy.props.EnumProperty(
        name="Pivot",
        items=(
            ("AUTO", "Auto Bounds", "Use center of calculated bounds"),
            ("ORIGIN", "Object Origin", "Use target object origin"),
            ("CURSOR", "3D Cursor", "Use scene cursor"),
            ("CUSTOM", "Custom", "Use custom world-space pivot"),
        ),
        default="AUTO",
    )
    custom_pivot: bpy.props.FloatVectorProperty(name="Custom Pivot", size=3, subtype="XYZ", default=(0.0, 0.0, 0.0))


class SBK_Settings(bpy.types.PropertyGroup):
    resolution_x: bpy.props.IntProperty(name="Width", default=128, min=1, max=8192)
    resolution_y: bpy.props.IntProperty(name="Height", default=128, min=1, max=8192)
    pixels_per_unit: bpy.props.FloatProperty(name="Pixels Per Unit", default=100.0, min=0.01)
    output_dir: bpy.props.StringProperty(name="Output Directory", subtype="DIR_PATH", default="//sprite_bake")
    naming_template: bpy.props.StringProperty(
        name="Name Template",
        default="{item}_{action}_{direction}_{frame}_{pass}",
    )
    camera_mode: bpy.props.EnumProperty(
        name="Camera",
        items=(
            ("ORTHO", "Orthographic", "Orthographic sprite camera"),
            ("WEAK_PERSPECTIVE", "Weak Perspective", "Long lens perspective camera"),
        ),
        default="ORTHO",
    )
    margin: bpy.props.FloatProperty(name="Margin", description="Framing margin ratio", default=0.12, min=0.0, max=1.0)
    frame_step: bpy.props.IntProperty(name="Frame Step", default=1, min=1, max=100)
    direction_strategy: bpy.props.EnumProperty(
        name="Direction Strategy",
        items=(
            ("ROTATE_TARGET", "Rotate Target", "Keep the camera fixed and rotate exported objects"),
            ("CAMERA_ORBIT", "Orbit Camera", "Keep objects fixed and orbit the temporary camera"),
        ),
        default="ROTATE_TARGET",
    )
    use_albedo: bpy.props.BoolProperty(name="Albedo", default=True)
    use_normal: bpy.props.BoolProperty(name="NormalMap", default=True)
    use_mask: bpy.props.BoolProperty(name="MaskTex", default=True)
    unity_names: bpy.props.BoolProperty(name="Unity Secondary Texture Names", default=True)
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
