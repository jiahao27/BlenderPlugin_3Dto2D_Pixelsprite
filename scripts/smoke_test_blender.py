from __future__ import annotations

import importlib
import hashlib
import json
import shutil
import sys
import tempfile
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
        output_dir = Path(tempfile.gettempdir()) / "sprite_baker_smoke"
        if output_dir.exists():
            shutil.rmtree(output_dir)
        output_dir.mkdir(parents=True)

        clear_scene()
        cube = create_cube_scene()
        action = create_action(cube)
        configure_camera_baker(cube, action, output_dir)

        from sprite_baker.baker import SpriteBaker

        bpy.ops.sprite_baker.create_bake_camera()
        count = SpriteBaker(bpy.context).export_all()
        if count <= 0:
            raise RuntimeError("No files were exported.")

        pngs = list(output_dir.rglob("*.png"))
        metadata = list(output_dir.rglob("metadata.json"))
        if len(pngs) < 6:
            raise RuntimeError(f"Expected multiple PNG files, found {len(pngs)}.")
        if not metadata:
            raise RuntimeError("metadata.json was not written.")
        camera_albedo = sorted((output_dir / "Camera").rglob("*_Albedo.png"))
        camera_hashes = {hashlib.sha256(path.read_bytes()).hexdigest() for path in camera_albedo}
        if len(camera_albedo) > 1 and len(camera_hashes) == 1:
            raise RuntimeError("Camera bake frames are identical; animation did not advance.")

        with metadata[0].open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        for key in ("frame_size", "frame_count", "pivot_px", "pixels_per_unit", "action", "directions"):
            if key not in data:
                raise RuntimeError(f"metadata.json missing key: {key}")

        configure_batch_baker(cube, action, output_dir / "batch")
        batch_count = SpriteBaker(bpy.context).export_all()
        if batch_count <= 0:
            raise RuntimeError("Batch mode exported no files.")

        configure_pixel_baker(cube, output_dir / "pixel")
        bpy.ops.sprite_baker.create_bake_camera()
        settings = bpy.context.scene.sprite_baker_settings
        if (settings.resolution_x, settings.resolution_y) != (64, 64):
            raise RuntimeError("Pixel canvas preset did not update the bake resolution.")
        if not settings.bake_camera or not settings.bake_camera.data.background_images:
            raise RuntimeError("Pixel grid background was not attached to the bake camera.")
        pixel_count = SpriteBaker(bpy.context).export_all()
        if pixel_count <= 0:
            raise RuntimeError("Pixel mode exported no files.")
        atlases = list((output_dir / "pixel").rglob("*_Atlas.png"))
        if len(atlases) < 3:
            raise RuntimeError("Sprite atlas files were not generated for all enabled passes.")

        print(f"Sprite Baker smoke test passed: {count + batch_count + pixel_count} files in {output_dir}")
    finally:
        addon.unregister()


def clear_scene() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()


def create_cube_scene():
    bpy.ops.mesh.primitive_cube_add(size=1.0)
    cube = bpy.context.object
    cube.name = "SmokeCube"
    mat = bpy.data.materials.new("SmokeMaterial")
    mat.diffuse_color = (0.8, 0.2, 0.1, 1.0)
    cube.data.materials.append(mat)
    cube.sprite_baker_mask.enabled = True
    cube.sprite_baker_mask.r = 1.0
    cube.sprite_baker_mask.a = 1.0
    return cube


def create_action(obj):
    obj.animation_data_create()
    action = bpy.data.actions.new("SmokeAction")
    obj.animation_data.action = action
    bpy.context.scene.frame_set(1)
    obj.location.x = 0.0
    obj.keyframe_insert(data_path="location", frame=1)
    bpy.context.scene.frame_set(2)
    obj.location.x = 0.25
    obj.keyframe_insert(data_path="location", frame=2)
    obj.animation_data.action = action
    return action


def reset_items(settings):
    settings.export_items.clear()
    settings.active_export_item_index = 0


def configure_camera_baker(cube, action, output_dir):
    settings = bpy.context.scene.sprite_baker_settings
    settings.output_dir = str(output_dir)
    settings.resolution_x = 32
    settings.resolution_y = 32
    settings.bake_mode = "CAMERA"
    settings.use_albedo = True
    settings.use_normal = True
    settings.use_mask = True
    settings.camera_source = "VISIBLE_BAKE_CAMERA"
    settings.frame_sampling = "FRAME_COUNT"
    settings.bake_frame_count = 3
    settings.frame_start = 1
    settings.frame_end = 2
    settings.camera_animation_target = cube
    settings.camera_action = action
    settings.enable_pixel_bake = False
    settings.merge_atlas = False
    reset_items(settings)


def configure_batch_baker(cube, action, output_dir):
    settings = bpy.context.scene.sprite_baker_settings
    settings.output_dir = str(output_dir)
    settings.bake_mode = "BATCH"
    settings.direction_strategy = "ROTATE_TARGET"
    settings.frame_sampling = "FRAME_COUNT"
    settings.bake_frame_count = 3
    settings.enable_pixel_bake = False
    settings.merge_atlas = False
    reset_items(settings)
    item = settings.export_items.add()
    item.name = "SmokeCube"
    item.target_type = "OBJECT"
    item.target_object = cube
    item.animation_mode = "ACTIONS"
    item.direction_preset = "FOUR"
    slot = item.actions.add()
    slot.action = action
    from sprite_baker.operators import generate_directions_for_item

    generate_directions_for_item(item)


def configure_pixel_baker(cube, output_dir):
    settings = bpy.context.scene.sprite_baker_settings
    settings.output_dir = str(output_dir)
    settings.bake_mode = "CAMERA"
    settings.frame_start = 1
    settings.frame_end = 2
    settings.frame_sampling = "FRAME_COUNT"
    settings.bake_frame_count = 4
    settings.enable_pixel_bake = True
    settings.pixel_canvas_preset = "64"
    settings.pixel_grid_opacity = 0.42
    settings.merge_atlas = True
    reset_items(settings)


if __name__ == "__main__":
    main()
