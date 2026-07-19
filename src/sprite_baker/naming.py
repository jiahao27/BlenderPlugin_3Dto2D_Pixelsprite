import re
from pathlib import Path


PASS_LABELS = {
    "ALBEDO": "Albedo",
    "NORMAL": "NormalMap",
    "MASK": "MaskTex",
}


def slugify(value):
    value = str(value or "unnamed").strip()
    value = re.sub(r"[^\w.-]+", "_", value, flags=re.UNICODE)
    return value.strip("._") or "unnamed"


def blend_abspath(path, bpy_module):
    return Path(bpy_module.path.abspath(path)).resolve()


def frame_name(settings, item_name, action_name, direction_name, frame, pass_id):
    pass_label = PASS_LABELS[pass_id]
    raw = settings.naming_template.format(
        **{
            "item": slugify(item_name),
            "action": slugify(action_name),
            "direction": slugify(direction_name),
            "frame": f"{frame:04d}",
            "pass": pass_label,
        }
    )
    if not raw.endswith(f"_{pass_label}"):
        raw = f"{raw}_{pass_label}"
    return f"{slugify(raw)}.png"
