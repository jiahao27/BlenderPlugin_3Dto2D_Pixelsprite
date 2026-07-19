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

        settings = bpy.context.scene.sprite_baker_pixel_tools
        settings.resolution_preset = "32"
        bpy.ops.sprite_baker.apply_render_settings()
        bpy.ops.sprite_baker.create_front_pixel_camera()
        settings.pixel_camera_type = "ISO"
        bpy.ops.sprite_baker.create_selected_pixel_camera()
        bpy.ops.sprite_baker.cleanup_grid_images()

        for material_type in ("FLAT", "FLAT_UV", "TOON", "IMAGE_PIXEL"):
            settings.material_type = material_type
            bpy.ops.sprite_baker.create_pixel_material()

        bpy.ops.sprite_baker.setup_outline()
        bpy.ops.sprite_baker.remove_outline()
        bpy.ops.sprite_baker.setup_viewport_pixel_preview()
        bpy.ops.sprite_baker.remove_viewport_pixel_preview()

        if not bpy.data.materials.get("SBK 平面色"):
            raise RuntimeError("像素材质没有创建成功。")
        if not any(camera.name.startswith("SBK 正面") for camera in bpy.data.objects if camera.type == "CAMERA"):
            raise RuntimeError("正面像素相机没有创建成功。")
        if not any(camera.name.startswith("SBK 等距") for camera in bpy.data.objects if camera.type == "CAMERA"):
            raise RuntimeError("等距像素相机没有创建成功。")

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
