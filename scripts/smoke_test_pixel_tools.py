from __future__ import annotations

import importlib
import sys
from pathlib import Path

import bpy


ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT / "src"
ADDON_NAME = "sprite_baker"


def main() -> None:
    sys.path.insert(0, str(SRC_DIR))
    addon = importlib.import_module(ADDON_NAME)
    addon.register()
    try:
        clear_scene()
        cube = create_cube()
        bpy.ops.object.select_all(action="DESELECT")
        cube.select_set(True)
        bpy.context.view_layer.objects.active = cube

        pixel_settings = bpy.context.scene.sprite_baker_pixel_tools
        pixel_settings.resolution_preset = "32"
        bpy.context.scene.render.resolution_x = 32
        bpy.context.scene.render.resolution_y = 32

        for material_type in ("FLAT", "FLAT_UV", "TOON", "IMAGE_PIXEL"):
            pixel_settings.material_type = material_type
            bpy.ops.sprite_baker.create_pixel_material()

        settings = bpy.context.scene.sprite_baker_settings
        settings.enable_pixel_bake = True
        settings.pixel_preview_scale = 0.25
        bpy.ops.sprite_baker.setup_viewport_pixel_preview()
        bpy.ops.sprite_baker.update_viewport_preview_resolution()
        bpy.ops.sprite_baker.remove_viewport_pixel_preview()

        if not bpy.data.materials.get("SBK 平面色"):
            raise RuntimeError("像素材质没有创建成功。")

        print("Sprite Baker pixel tools smoke test passed.")
    finally:
        addon.unregister()


def clear_scene() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()


def create_cube():
    bpy.ops.mesh.primitive_cube_add(size=1.0)
    cube = bpy.context.object
    cube.name = "PixelToolsCube"
    return cube


if __name__ == "__main__":
    main()
