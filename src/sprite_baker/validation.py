from pathlib import Path

import bpy


def get_active_item(settings):
    if not settings.export_items:
        return None
    index = min(settings.active_export_item_index, len(settings.export_items) - 1)
    return settings.export_items[index]


def target_objects(item):
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

    if not settings.export_items:
        errors.append("请至少添加一个导出项。")

    for item in settings.export_items:
        objects = target_objects(item)
        if not objects:
            errors.append(f"导出项“{item.name}”没有可渲染目标。")
        if item.animation_mode == "ACTIONS" and not any(slot.action for slot in item.actions):
            errors.append(f"导出项“{item.name}”使用动作模式，但没有指定动作。")
        if item.direction_preset == "CUSTOM":
            try:
                parse_custom_directions(item.custom_directions)
            except ValueError as exc:
                errors.append(f"导出项“{item.name}”的自定义方向无效：{exc}")

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
