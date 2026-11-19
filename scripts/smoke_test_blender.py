from __future__ import annotations

import importlib
import hashlib
import json
import math
import shutil
import sys
import tempfile
from pathlib import Path

import bpy
import numpy as np


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
        bpy.ops.sprite_baker.generate_directions()
        count = SpriteBaker(bpy.context).export_all()
        if count <= 0:
            raise RuntimeError("No files were exported.")

        pngs = list(output_dir.rglob("*.png"))
        metadata = list(output_dir.rglob("metadata.json"))
        if len(pngs) < 6:
            raise RuntimeError(f"Expected multiple PNG files, found {len(pngs)}.")
        if not metadata:
            raise RuntimeError("metadata.json was not written.")
        camera_directions = {path.parent.parent.name for path in (output_dir / "Camera").rglob("*_NormalMap.png")}
        if camera_directions != {"dir_000", "dir_090", "dir_180", "dir_270"}:
            raise RuntimeError(f"Camera bake directions were not exported: {camera_directions}")
        assert_unity_normal_map_encoding(next((output_dir / "Camera").rglob("*_NormalMap.png")))
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

        high_count = verify_supersampling(output_dir / "supersampled")
        packed_count = verify_packed_normals(output_dir / "packed")
        total = count + batch_count + pixel_count + high_count + packed_count
        print(f"Sprite Baker smoke test passed: {total} files in {output_dir}")
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
    settings.unity_2d_normal_map = True
    settings.normal_map_edge_padding = True
    settings.use_mask = True
    settings.camera_source = "VISIBLE_BAKE_CAMERA"
    settings.direction_preset = "FOUR"
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
    settings.direction_preset = "SINGLE"
    bpy.ops.sprite_baker.generate_directions()
    reset_items(settings)


def assert_unity_normal_map_encoding(path):
    image = bpy.data.images.load(str(path), check_existing=False)
    try:
        image.colorspace_settings.name = "Non-Color"
        width, height = image.size
        index = ((height // 2) * width + (width // 2)) * 4
        red, green, blue, alpha = image.pixels[index:index + 4]
        if alpha <= 0.5 or not (0.45 <= red <= 0.55 and 0.45 <= green <= 0.55 and blue >= 0.95):
            raise RuntimeError(
                "NormalMap is not stored as Unity-compatible linear vector data: "
                f"{(red, green, blue, alpha)}"
            )
    finally:
        bpy.data.images.remove(image)


def verify_supersampling(output_dir):
    from sprite_baker.baker import SpriteBaker
    from sprite_baker.validation import processing_errors

    scene = bpy.context.scene
    settings = scene.sprite_baker_settings
    settings.output_dir = str(output_dir)
    settings.pixel_canvas_preset = "CUSTOM"
    settings.resolution_x = 24
    settings.resolution_y = 20
    settings.pixel_sampling = "SUPERSAMPLE"
    settings.pixel_sample_factor = 3
    settings.pixel_downsample_method = "TOP_LEFT"
    settings.color_quantization = "FIXED"
    settings.fixed_palette = "#1357AB, #F3AC62"
    settings.pack_mask_in_normal = True

    settings.use_albedo = False
    settings.use_normal = False
    if not processing_errors(settings):
        raise RuntimeError("High sampling must reject MaskTex-only export.")
    settings.use_albedo = True
    settings.use_normal = True

    render = scene.render
    original = (render.resolution_x, render.resolution_y, render.use_compositing, render.dither_intensity)
    count = SpriteBaker(bpy.context).export_all()
    if count != 8 or list(output_dir.rglob("*MaskTex*.png")):
        raise RuntimeError("High sampling must export both supported channels and skip MaskTex.")
    if original != (render.resolution_x, render.resolution_y, render.use_compositing, render.dither_intensity):
        raise RuntimeError("Blender render settings were not restored.")
    data = json.loads(next(output_dir.rglob("metadata.json")).read_text(encoding="utf-8"))
    if data["frame_size"] != [24, 20] or len(data["atlas_files"]) != 2 or "normal_map_encoding" in data:
        raise RuntimeError("The metadata must record the final dimensions and both supported atlases.")
    if any(entry["atlas_size"] != [48, 40] for entry in data["atlas_files"]):
        raise RuntimeError("The atlases did not use the downsampled tile sizes.")
    albedo = next(output_dir.rglob("*_Albedo.png"))
    normal = next(output_dir.rglob("*_NormalMap.png"))
    assert_unity_normal_map_encoding(normal)
    pixels = read_rgba_bytes(albedo)
    normal_pixels = read_rgba_bytes(normal)
    if pixels.shape != (20, 24, 4) or normal_pixels.shape != pixels.shape:
        raise RuntimeError("Albedo and NormalMap did not export at the requested dimensions.")
    visible = pixels[..., 3] > 0
    colors = {tuple(rgb) for rgb in pixels[visible, :3]}
    if not colors or not colors <= {(19, 87, 171), (243, 172, 98)} or np.all(visible):
        raise RuntimeError(f"Unexpected fixed palette colors or coverage: {colors}")
    atlas = read_rgba_bytes(next(output_dir.rglob("*_Albedo_Atlas.png")))
    if atlas.shape != (40, 48, 4) or not {tuple(rgb) for rgb in atlas[atlas[..., 3] > 0, :3]} <= colors:
        raise RuntimeError("The Albedo atlas did not preserve the fixed palette.")

    settings.pixel_sampling = "DIRECT"
    settings.pack_mask_in_normal = False
    settings.color_quantization = "KMEANS"
    settings.kmeans_colors = 1
    files = SpriteBaker(bpy.context).render_preview()
    if not any(path.endswith("_MaskTex.png") for path in files):
        raise RuntimeError("Switching back to direct sampling must restore MaskTex.")
    albedo_preview = next(path for path in files if path.endswith("_Albedo.png"))
    pixels = read_rgba_bytes(output_dir / "_preview" / albedo_preview)
    colors = np.unique(pixels[pixels[..., 3] > 0, :3], axis=0)
    if pixels.shape != (20, 24, 4) or len(colors) != 1:
        raise RuntimeError("Direct sampling K-means preview did not output a one-color Albedo.")
    return count


def verify_packed_normals(output_dir):
    from sprite_baker.baker import SpriteBaker

    clear_scene()
    mesh = bpy.data.meshes.new("SmokePackedMesh")
    mesh.from_pydata(
        [(-1, 0, -0.5), (0, 0, -0.5), (0, 0, 0.5), (-1, 0, 0.5), (1, 0, -0.5), (1, 0, 0.5)],
        [],
        [(0, 1, 2, 3), (1, 4, 5, 2)],
    )
    obj = bpy.data.objects.new("SmokePacked", mesh)
    bpy.context.scene.collection.objects.link(obj)
    left, right = [bpy.data.materials.new(name) for name in ("PackedLeft", "PackedRight")]
    mesh.materials.append(None)
    mesh.materials.append(right)
    obj.material_slots[0].link = "OBJECT"
    obj.material_slots[0].material = left
    mesh.polygons[1].material_index = 1
    left.sprite_baker_mask.enabled = True
    left.sprite_baker_mask.r = 0.25
    obj.sprite_baker_mask.enabled = True
    obj.sprite_baker_mask.r = 0.75

    scene = bpy.context.scene
    settings = scene.sprite_baker_settings
    settings.output_dir = str(output_dir)
    settings.camera_action = None
    settings.camera_animation_target = None
    settings.frame_end = settings.frame_start
    settings.resolution_x = 48
    settings.resolution_y = 28
    settings.use_albedo = True
    settings.color_quantization = "NONE"
    settings.use_mask = False
    settings.normal_map_edge_padding = True
    scene.render.dither_intensity = 0
    camera_data = bpy.data.cameras.new("SmokePackedCamera")
    camera_data.type = "ORTHO"
    camera_data.ortho_scale = 2.25
    camera = bpy.data.objects.new("SmokePackedCamera", camera_data)
    scene.collection.objects.link(camera)
    camera.location = (0, -10, 0)
    camera.rotation_euler = (math.pi / 2, 0, 0)
    scene.camera = settings.bake_camera = camera
    bpy.context.view_layer.update()

    preview = SpriteBaker(bpy.context).render_preview()
    regular_name = next(path for path in preview if path.endswith("_NormalMap.png"))
    regular_path = output_dir / "_preview" / regular_name
    assert_unity_normal_map_encoding(regular_path)
    regular = read_rgba_bytes(regular_path)

    settings.pack_mask_in_normal = True
    count = SpriteBaker(bpy.context).export_all()
    data = json.loads(next(output_dir.rglob("metadata.json")).read_text(encoding="utf-8"))
    if data.get("normal_map_encoding") != "XY_MASK_R" or list(output_dir.rglob("*MaskTex*.png")):
        raise RuntimeError("Packed encoding must be documented even without a separate MaskTex.")

    normal = next(path for path in output_dir.rglob("*_NormalMap.png") if "_preview" not in path.parts)
    atlas = next(output_dir.rglob("*_NormalMap_Atlas.png"))
    packed = read_rgba_bytes(normal)
    np.testing.assert_array_equal(packed[..., 3], regular[..., 3])
    np.testing.assert_allclose(packed[..., :2].astype(int), regular[..., :2].astype(int), atol=1, rtol=0)
    height, width = packed.shape[:2]
    if tuple(packed[height // 2, [width // 4, width * 3 // 4], 2]) != (64, 191):
        raise RuntimeError("Packed mask values were assigned to the wrong faces.")
    for image in (packed, read_rgba_bytes(atlas)):
        blue = set(image[..., 2][image[..., 3] == 255].tolist())
        if blue != {64, 191}:
            raise RuntimeError(f"Packed B did not preserve material/object mask weights: {blue}")
    if [face.material_index for face in mesh.polygons] != [0, 1]:
        raise RuntimeError("Baking changed the mesh face material indices.")
    if obj.material_slots[0].link != "OBJECT" or obj.material_slots[0].material != left or mesh.materials[1] != right:
        raise RuntimeError("Baking did not restore object and mesh materials.")
    return count


def read_rgba_bytes(path):
    image = bpy.data.images.load(str(path), check_existing=False)
    try:
        image.colorspace_settings.name = "Non-Color"
        width, height = image.size
        rgba = np.empty((height, width, 4), dtype=np.float32)
        image.pixels.foreach_get(rgba.ravel())
        return np.rint(rgba * 255).astype(np.uint8)
    finally:
        bpy.data.images.remove(image)


if __name__ == "__main__":
    main()
