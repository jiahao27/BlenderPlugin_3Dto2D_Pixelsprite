from pathlib import Path

import bpy


def get_active_item(settings):
    if not settings.export_items:
        return None
    index = min(settings.active_export_item_index, len(settings.export_items) - 1)
    return settings.export_items[index]


def target_objects(item):
    if getattr(item, "target_type", None) == "SCENE":
        return [obj for obj in bpy.context.scene.objects if obj.type == "MESH" and not obj.hide_render]
    if item.target_type == "OBJECT":
        return [item.target_object] if item.target_object else []
    if not item.target_collection:
        return []
    return [obj for obj in item.target_collection.all_objects if obj.type == "MESH"]


def validate_settings(context, preview=False):
    settings = context.scene.sprite_baker_settings
    errors = []

    if not (settings.use_albedo or settings.use_normal or settings.use_mask):
        errors.append("至少需要启用一个导出通道。")

    output_dir = Path(bpy.path.abspath(settings.output_dir))
    parent = output_dir if preview else output_dir.parent
    if not parent.exists():
        errors.append(f"输出目录的上级目录不存在：{parent}")

    if settings.resolution_x <= 0 or settings.resolution_y <= 0:
        errors.append("分辨率必须大于 0。")

    if settings.bake_mode == "CAMERA":
        camera = settings.bake_camera or context.scene.camera
        if camera is None or camera.type != "CAMERA":
            errors.append("相机烘焙模式需要一个烘焙相机。请点击“创建/更新烘焙相机”。")
        if settings.frame_end < settings.frame_start:
            errors.append("结束帧不能小于起始帧。")
        if settings.camera_action is not None and settings.camera_animation_target is None:
            errors.append("相机烘焙指定了动作，但没有指定动画对象。")
        return errors

    if not settings.export_items:
        errors.append("批量动作烘焙模式需要至少一个烘焙目标。")

    for item in settings.export_items:
        objects = target_objects(item)
        if not objects:
            errors.append(f"烘焙目标“{item.name}”没有可渲染对象。")
        if item.animation_mode == "ACTIONS" and not any(slot.action for slot in item.actions):
            errors.append(f"烘焙目标“{item.name}”使用动作模式，但没有指定动作。")
        if item.direction_preset == "CUSTOM":
            try:
                parse_custom_directions(item.custom_directions)
            except ValueError as exc:
                errors.append(f"烘焙目标“{item.name}”的自定义方向无效：{exc}")

    return errors


def parse_custom_directions(value):
    angles = []
    for part in value.split(","):
        text = part.strip()
        if not text:
            continue
        angles.append(float(text))
    if not angles:
        raise ValueError("没有填写角度")
    return angles
