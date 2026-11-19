from pathlib import Path

import bpy

from .atlas import is_prime
from .bake_options import MAX_SUPERSAMPLE_PIXELS, enabled_passes, is_supersampled, output_size, supersample_factor
from .image_processing import parse_palette


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
    errors = processing_errors(settings)

    output_dir = Path(bpy.path.abspath(settings.output_dir))
    parent = output_dir if preview else output_dir.parent
    if not parent.exists():
        errors.append(f"输出目录的上级目录不存在：{parent}")

    if settings.bake_mode == "CAMERA":
        camera = settings.bake_camera or context.scene.camera
        if camera is None or camera.type != "CAMERA":
            errors.append("相机烘焙模式需要一个烘焙相机。请点击“创建/更新烘焙相机”。")
        if settings.frame_end < settings.frame_start:
            errors.append("结束帧不能小于起始帧。")
        if settings.camera_action is not None and settings.camera_animation_target is None:
            errors.append("相机烘焙指定了动作，但没有指定动画对象。")
        if settings.direction_preset == "CUSTOM":
            try:
                parse_custom_directions(settings.custom_directions)
            except ValueError as exc:
                errors.append(f"相机烘焙的自定义方向无效：{exc}")
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


def processing_errors(settings):
    errors = []
    if not enabled_passes(settings):
        if is_supersampled(settings):
            errors.append("高采样至少需要启用 Albedo 或 NormalMap；MaskTex 暂不支持高采样。")
        else:
            errors.append("至少需要启用一个导出通道。")

    width, height = output_size(settings)
    if width <= 0 or height <= 0:
        errors.append("分辨率必须大于 0。")
    factor = supersample_factor(settings)
    if min(width, height) > 0 and min(width, height) * factor < 4:
        errors.append("Blender 渲染宽高至少为 4 像素，请提高画布分辨率或采样倍数。")
    if factor > 1 and width * height * factor ** 2 > MAX_SUPERSAMPLE_PIXELS:
        errors.append(f"高采样渲染尺寸 {width * factor} × {height * factor} 超过 16,777,216 像素，请降低分辨率或倍数。")

    if settings.use_albedo and settings.color_quantization == "FIXED":
        try:
            parse_palette(settings.fixed_palette)
        except ValueError as exc:
            errors.append(f"Albedo 调色板无效：{exc}")
    return errors


def processing_warnings(settings):
    if is_supersampled(settings) and settings.use_mask:
        return ["高采样模式将跳过 MaskTex；切回低采样可恢复遮罩导出。"]
    return []


def atlas_warnings(context):
    settings = context.scene.sprite_baker_settings
    warnings = []

    if settings.bake_mode == "CAMERA":
        count = sampled_frame_count(settings, settings.frame_start, max(settings.frame_start, settings.frame_end))
        if is_prime(count):
            warnings.append(atlas_prime_message(settings, f"相机烘焙将导出 {count} 帧"))
        return warnings

    for item in settings.export_items:
        if item.animation_mode == "STATIC":
            count = sampled_frame_count(settings, item.frame_start, max(item.frame_start, item.frame_end))
            if is_prime(count):
                warnings.append(atlas_prime_message(settings, f"烘焙目标“{item.name}”的静态序列将导出 {count} 帧"))
            continue

        for slot in item.actions:
            action = slot.action
            if action is None:
                continue
            if item.use_action_frame_range:
                start, end = action.frame_range
                frame_start = int(round(start))
                frame_end = int(round(end))
            else:
                frame_start = item.frame_start
                frame_end = max(item.frame_start, item.frame_end)
            count = sampled_frame_count(settings, frame_start, frame_end)
            if is_prime(count):
                warnings.append(atlas_prime_message(settings, f"动作“{action.name}”将导出 {count} 帧"))

    return warnings


def sampled_frame_count(settings, frame_start, frame_end):
    if settings.frame_sampling == "FRAME_COUNT":
        return max(1, settings.bake_frame_count)
    return len(range(frame_start, frame_end + 1, settings.frame_step))


def atlas_prime_message(settings, prefix):
    if settings.merge_atlas:
        return f"{prefix}；这是质数，无法按当前规则合并为大图，本次将只输出序列帧。"
    return f"{prefix}；这是质数，之后难以按当前规则合并为大图。"


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
