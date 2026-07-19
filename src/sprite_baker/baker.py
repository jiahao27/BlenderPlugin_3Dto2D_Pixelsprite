import json
from pathlib import Path

import bpy

from .camera import configure_camera, make_camera, object_bounds, pivot_for_item, rotate_objects
from .materials import setup_albedo, setup_mask, setup_normal
from .naming import PASS_LABELS, blend_abspath, frame_name, slugify
from .state import SceneState, remove_temp_data
from .validation import get_active_item, target_objects


class SpriteBaker:
    def __init__(self, context):
        self.context = context
        self.scene = context.scene
        self.settings = self.scene.sprite_baker_settings

    def render_preview(self):
        item = get_active_item(self.settings)
        if item is None:
            return []
        ensure_directions(item)
        action_name, action, frame_start, _frame_end = self.action_jobs(item)[0]
        direction = item.directions[min(item.active_direction_index, len(item.directions) - 1)]
        output_root = blend_abspath(self.settings.output_dir, bpy) / "_preview"
        return self.render_job(item, action_name, action, direction, frame_start, output_root, preview=True)

    def export_all(self):
        output_root = blend_abspath(self.settings.output_dir, bpy)
        output_root.mkdir(parents=True, exist_ok=True)
        written = 0
        for item in self.settings.export_items:
            ensure_directions(item)
            for action_name, action, frame_start, frame_end in self.action_jobs(item):
                metadata = []
                for direction in item.directions:
                    for frame in range(frame_start, frame_end + 1, self.settings.frame_step):
                        files = self.render_job(item, action_name, action, direction, frame, output_root)
                        written += len(files)
                        metadata.append(
                            {
                                "frame": frame,
                                "direction": direction.name,
                                "direction_deg": direction.angle,
                                "pass_files": files,
                            }
                        )
                self.write_metadata(output_root, item, action_name, metadata)
        return written

    def render_job(self, item, action_name, action, direction, frame, output_root, preview=False):
        objects = target_objects(item)
        armature = item.armature
        state_objects = list({obj for obj in objects + ([armature] if armature else []) if obj})
        state = SceneState(self.scene, state_objects)
        files = []
        camera = None
        try:
            remove_temp_data()
            self.configure_scene_for_render(objects)
            self.apply_action(item, action)
            self.scene.frame_set(frame)
            bounds = object_bounds(objects)
            pivot = pivot_for_item(self.context, item, objects, bounds)
            if self.settings.direction_strategy == "ROTATE_TARGET":
                rotate_objects(objects, pivot, direction.angle)
                bounds = object_bounds(objects)
            camera = make_camera(self.scene, self.settings)
            _, scale = configure_camera(self.scene, camera, self.settings, bounds, direction.angle)

            original_materials = capture_materials(objects)
            pass_ids = enabled_passes(self.settings)
            for pass_id in pass_ids:
                restore_material_slots(objects, original_materials)
                self.setup_pass(objects, pass_id)
                filepath = self.output_path(output_root, item, action_name, direction, frame, pass_id, preview)
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
        self.scene.render.resolution_x = self.settings.resolution_x
        self.scene.render.resolution_y = self.settings.resolution_y
        self.scene.render.film_transparent = True
        self.scene.render.image_settings.file_format = "PNG"
        self.scene.render.image_settings.color_mode = "RGBA"
        self.scene.render.image_settings.color_depth = "8"
        self.scene.view_settings.view_transform = "Standard"
        self.scene.view_settings.look = "None"
        self.scene.view_settings.exposure = 0.0
        self.scene.view_settings.gamma = 1.0

        visible = set(objects)
        for obj in bpy.data.objects:
            if obj.type == "MESH":
                obj.hide_render = obj not in visible

    def apply_action(self, item, action):
        target = item.armature or item.target_object
        if target is None:
            return
        target.animation_data_create()
        target.animation_data.action = action

    def action_jobs(self, item):
        if item.animation_mode == "STATIC":
            return [("Static", None, self.scene.frame_current, self.scene.frame_current)]

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
            "frame_count": len({entry["frame"] for entry in frames}),
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
