import json
from pathlib import Path

import bpy

from .camera import configure_camera, make_camera, make_visible_bake_camera, object_bounds, pivot_for_item, rotate_objects
from .materials import setup_albedo, setup_mask, setup_normal
from .naming import PASS_LABELS, blend_abspath, frame_name, slugify
from .pixel_tools.viewport_preview import remove_viewport_pixel_preview, setup_viewport_pixel_preview
from .state import SceneState, remove_temp_data
from .validation import get_active_item, target_objects


class SpriteBaker:
    def __init__(self, context):
        self.context = context
        self.scene = context.scene
        self.settings = self.scene.sprite_baker_settings

    def render_preview(self):
        item = self.preview_item()
        ensure_directions(item)
        action_name, action, frame_start, _frame_end = self.action_jobs(item)[0]
        direction = item.directions[min(item.active_direction_index, len(item.directions) - 1)]
        output_root = blend_abspath(self.settings.output_dir, bpy) / "_preview"
        return self.render_job(item, action_name, action, direction, frame_start, output_root, preview=True)

    def export_all(self):
        output_root = blend_abspath(self.settings.output_dir, bpy)
        output_root.mkdir(parents=True, exist_ok=True)
        written = 0
        for item in self.export_items():
            ensure_directions(item)
            for action_name, action, frame_start, frame_end in self.action_jobs(item):
                metadata = []
                for direction in item.directions:
                    for source_frame, output_frame in self.frame_jobs(frame_start, frame_end):
                        files = self.render_job(
                            item,
                            action_name,
                            action,
                            direction,
                            source_frame,
                            output_root,
                            output_frame=output_frame,
                        )
                        written += len(files)
                        metadata.append(
                            {
                                "frame": output_frame,
                                "source_frame": source_frame,
                                "direction": direction.name,
                                "direction_deg": direction.angle,
                                "pass_files": files,
                            }
                        )
                self.write_metadata(output_root, item, action_name, metadata)
        return written

    def export_items(self):
        if self.settings.bake_mode == "CAMERA" and not self.settings.export_items:
            return [CameraExportItem(self.context)]
        return list(self.settings.export_items)

    def preview_item(self):
        item = get_active_item(self.settings)
        if item is not None:
            return item
        if self.settings.bake_mode == "CAMERA":
            return CameraExportItem(self.context)
        raise RuntimeError("请先添加一个烘焙目标。")

    def render_job(self, item, action_name, action, direction, frame, output_root, preview=False, output_frame=None):
        objects = target_objects(item)
        armature = item.armature
        state_objects = list({obj for obj in objects + ([armature] if armature else []) if obj})
        state = SceneState(self.scene, state_objects)
        files = []
        camera = None
        try:
            remove_temp_data()
            self.configure_scene_for_render(objects)
            self.configure_pixel_compositor()
            self.apply_action(item, action)
            self.scene.frame_set(frame)
            bounds = object_bounds(objects)
            pivot = pivot_for_item(self.context, item, objects, bounds)
            if self.settings.direction_strategy == "ROTATE_TARGET":
                rotate_objects(objects, pivot, direction.angle)
                bounds = object_bounds(objects)
            if self.settings.bake_mode == "CAMERA":
                camera = self.settings.bake_camera or self.scene.camera
                if camera is None or camera.type != "CAMERA":
                    raise RuntimeError("相机烘焙需要一个烘焙相机。")
                self.scene.camera = camera
                scale = camera.data.ortho_scale if camera.data.type == "ORTHO" else 0.0
            else:
                if self.settings.camera_source == "VISIBLE_BAKE_CAMERA":
                    camera = make_visible_bake_camera(self.scene, self.settings)
                else:
                    camera = make_camera(self.scene, self.settings)
                _, scale = configure_camera(self.scene, camera, self.settings, bounds, direction.angle)

            original_materials = capture_materials(objects)
            pass_ids = enabled_passes(self.settings)
            for pass_id in pass_ids:
                restore_material_slots(objects, original_materials)
                self.setup_pass(objects, pass_id)
                filepath = self.output_path(output_root, item, action_name, direction, output_frame or frame, pass_id, preview)
                filepath.parent.mkdir(parents=True, exist_ok=True)
                self.scene.render.filepath = str(filepath)
                bpy.ops.render.render(write_still=True)
                files.append(str(filepath.relative_to(output_root)))

            self._last_frame_size = (self.settings.resolution_x, self.settings.resolution_y)
            self._last_pivot_px = (self.settings.resolution_x // 2, self.settings.resolution_y // 2)
            self._last_scale = scale
            return files
        finally:
            state.restore()
            if self.settings.enable_pixel_bake:
                remove_viewport_pixel_preview(self.scene)
            remove_temp_data()

    def setup_pass(self, objects, pass_id):
        if pass_id == "ALBEDO":
            setup_albedo(objects)
        elif pass_id == "NORMAL":
            setup_normal(objects)
        elif pass_id == "MASK":
            setup_mask(objects)

    def configure_scene_for_render(self, objects):
        try:
            self.scene.render.engine = "BLENDER_EEVEE_NEXT"
        except TypeError:
            self.scene.render.engine = "BLENDER_EEVEE"
        if self.settings.enable_pixel_bake and self.settings.pixel_canvas_preset != "CUSTOM":
            size = int(self.settings.pixel_canvas_preset)
            self.settings.resolution_x = size
            self.settings.resolution_y = size
        self.scene.render.resolution_x = self.settings.resolution_x
        self.scene.render.resolution_y = self.settings.resolution_y
        self.scene.render.resolution_percentage = 100
        self.scene.render.film_transparent = True
        self.scene.render.image_settings.file_format = "PNG"
        self.scene.render.image_settings.color_mode = "RGBA"
        self.scene.render.image_settings.color_depth = "8"
        if hasattr(self.scene.render, "filter_size"):
            self.scene.render.filter_size = 0.0
        self.scene.view_settings.view_transform = "Standard"
        self.scene.view_settings.look = "None"
        self.scene.view_settings.exposure = 0.0
        self.scene.view_settings.gamma = 1.0

        visible = set(objects)
        for obj in bpy.data.objects:
            if obj.type == "MESH":
                obj.hide_render = obj not in visible

    def configure_pixel_compositor(self):
        if not self.settings.enable_pixel_bake:
            return
        preview_scale = 1.0
        if self.settings.pixel_canvas_preset == "CUSTOM":
            preview_scale = self.settings.pixel_preview_scale
        setup_viewport_pixel_preview(
            self.scene,
            preview_scale,
            self.settings.pixel_preview_offset_x,
            self.settings.pixel_preview_offset_y,
        )

    def apply_action(self, item, action):
        target = item.armature or item.target_object
        if target is None:
            return
        target.animation_data_create()
        target.animation_data.action = action

    def action_jobs(self, item):
        if self.settings.bake_mode == "CAMERA":
            start = self.settings.frame_start
            end = max(start, self.settings.frame_end)
            return [("Camera", None, start, end)]
        if item.animation_mode == "STATIC":
            return [("Static", None, item.frame_start, max(item.frame_start, item.frame_end))]

        jobs = []
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
                frame_end = item.frame_end
            jobs.append((action.name, action, frame_start, max(frame_start, frame_end)))
        return jobs

    def frame_jobs(self, frame_start, frame_end):
        if self.settings.frame_sampling == "FRAME_COUNT":
            count = max(1, self.settings.bake_frame_count)
            if count == 1:
                return [(frame_start, 1)]
            span = max(0, frame_end - frame_start)
            return [
                (int(round(frame_start + span * index / (count - 1))), index + 1)
                for index in range(count)
            ]
        return [
            (frame, frame)
            for frame in range(frame_start, frame_end + 1, self.settings.frame_step)
        ]

    def output_path(self, output_root, item, action_name, direction, frame, pass_id, preview):
        if preview:
            return output_root / PASS_LABELS[pass_id] / frame_name(
                self.settings, item.name, action_name, direction.name, frame, pass_id
            )
        return (
            output_root
            / slugify(item.name)
            / slugify(action_name)
            / slugify(direction.name)
            / PASS_LABELS[pass_id]
            / frame_name(self.settings, item.name, action_name, direction.name, frame, pass_id)
        )

    def write_metadata(self, output_root, item, action_name, frames):
        action_root = output_root / slugify(item.name) / slugify(action_name)
        action_root.mkdir(parents=True, exist_ok=True)
        data = {
            "frame_size": [self.settings.resolution_x, self.settings.resolution_y],
            "frame_count": max((entry["frame"] for entry in frames), default=0),
            "pivot_px": [self.settings.resolution_x // 2, self.settings.resolution_y // 2],
            "pixels_per_unit": self.settings.pixels_per_unit,
            "item": item.name,
            "action": action_name,
            "directions": frames,
        }
        with (action_root / "metadata.json").open("w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=2, ensure_ascii=False)


def enabled_passes(settings):
    passes = []
    if settings.use_albedo:
        passes.append("ALBEDO")
    if settings.use_normal:
        passes.append("NORMAL")
    if settings.use_mask:
        passes.append("MASK")
    return passes


def ensure_directions(item):
    if item.directions:
        return
    if not hasattr(item.directions, "clear"):
        return
    from .operators import generate_directions_for_item

    generate_directions_for_item(item)


def capture_materials(objects):
    materials = {}
    for obj in objects:
        if hasattr(obj.data, "materials"):
            materials[obj] = [mat for mat in obj.data.materials]
    return materials


def restore_material_slots(objects, original_materials):
    for mat in list(bpy.data.materials):
        if mat.name.startswith("SBK_TMP_"):
            bpy.data.materials.remove(mat, do_unlink=True)
    for obj in objects:
        if obj not in original_materials:
            continue
        obj.data.materials.clear()
        for mat in original_materials[obj]:
            obj.data.materials.append(mat)


class CameraExportItem:
    name = "Camera"
    target_type = "SCENE"
    target_object = None
    target_collection = None
    armature = None
    animation_mode = "STATIC"
    actions = ()
    direction_preset = "SINGLE"
    custom_directions = "0"
    use_action_frame_range = False
    pivot_mode = "AUTO"
    custom_pivot = (0.0, 0.0, 0.0)

    def __init__(self, context):
        self.context = context
        settings = context.scene.sprite_baker_settings
        self.frame_start = settings.frame_start
        self.frame_end = settings.frame_end
        self.directions = [CameraDirection()]


class CameraDirection:
    name = "camera"
    angle = 0.0
