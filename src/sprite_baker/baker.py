import json
from pathlib import Path
from tempfile import TemporaryDirectory

import bpy
from mathutils import Vector

from .atlas import build_sprite_atlas
from .bake_image import process_render
from .bake_options import enabled_passes, is_supersampled, output_size, packs_normal_mask, supersample_factor
from .camera import configure_camera, make_camera, make_visible_bake_camera, object_bounds, pivot_for_item, rotate_objects
from .image_processing import parse_palette
from .materials import albedo_materials, mask_materials, normal_materials
from .naming import PASS_LABELS, blend_abspath, frame_name, slugify
from .normal_map import expand_transparent_edge
from .pixel_tools.viewport_preview import remove_viewport_pixel_preview, setup_viewport_pixel_preview
from .state import SceneState, remove_temp_data
from .validation import get_active_item, processing_errors, target_objects


class SpriteBaker:
    def __init__(self, context):
        self.context = context
        self.scene = context.scene
        self.settings = self.scene.sprite_baker_settings

    def render_preview(self):
        self.prepare_image_processing()
        item = self.preview_item()
        ensure_directions(item)
        action_name, action, frame_start, _frame_end = self.action_jobs(item)[0]
        direction = item.directions[min(item.active_direction_index, len(item.directions) - 1)]
        output_root = blend_abspath(self.settings.output_dir, bpy) / "_preview"
        return self.render_job(item, action_name, action, direction, frame_start, output_root, preview=True)

    def export_all(self):
        self.prepare_image_processing()
        output_root = blend_abspath(self.settings.output_dir, bpy)
        output_root.mkdir(parents=True, exist_ok=True)
        written = 0
        for item in self.export_items():
            ensure_directions(item)
            for action_name, action, frame_start, frame_end in self.action_jobs(item):
                metadata = []
                frame_jobs = self.frame_jobs(frame_start, frame_end)
                fixed_framing = self.fixed_framing_for_action(item, action, item.directions, frame_jobs)
                for direction in item.directions:
                    for source_frame, output_frame in frame_jobs:
                        files = self.render_job(
                            item,
                            action_name,
                            action,
                            direction,
                            source_frame,
                            output_root,
                            output_frame=output_frame,
                            fixed_framing=fixed_framing,
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
                atlas_files = self.write_atlases(output_root, item, action_name, metadata)
                self.write_metadata(output_root, item, action_name, metadata, atlas_files)
        return written

    def prepare_image_processing(self):
        errors = processing_errors(self.settings)
        if errors:
            raise ValueError("\n".join(errors))

        self.frame_size = output_size(self.settings)
        self.sample_factor = supersample_factor(self.settings)
        self.palette_options = None
        if self.settings.use_albedo and self.settings.color_quantization == "FIXED":
            self.palette_options = {"palette": parse_palette(self.settings.fixed_palette)}
        elif self.settings.use_albedo and self.settings.color_quantization == "KMEANS":
            self.palette_options = {
                "k": self.settings.kmeans_colors,
                "max_iterations": self.settings.kmeans_iterations,
                "seed": self.settings.kmeans_seed,
            }

    def export_items(self):
        if self.settings.bake_mode == "CAMERA":
            if not self.settings.export_items:
                return [CameraExportItem(self.context)]
            return [CameraExportItem(self.context, source_item=item) for item in self.settings.export_items]
        return list(self.settings.export_items)

    def preview_item(self):
        item = get_active_item(self.settings)
        if self.settings.bake_mode == "CAMERA":
            return CameraExportItem(self.context, source_item=item)
        if item is not None:
            return item
        raise RuntimeError("请先添加一个烘焙目标。")

    def render_job(self, item, action_name, action, direction, frame, output_root, preview=False, output_frame=None, fixed_framing=None):
        objects = target_objects(item)
        armature = item.armature
        animation_target = self.animation_target_for_item(item)
        state_objects = list({
            obj
            for obj in objects
            + ([armature] if armature else [])
            + ([animation_target] if animation_target else [])
            + ([self.settings.bake_camera] if self.settings.bake_camera else [])
            + ([self.scene.camera] if self.scene.camera else [])
            if obj
        })
        state = SceneState(self.scene, state_objects)
        files = []
        camera = None
        try:
            remove_temp_data()
            self.configure_scene_for_render(objects)
            self.configure_pixel_compositor()
            self.apply_action(item, action)
            self.scene.frame_set(frame)
            self.context.view_layer.update()
            bounds = object_bounds(objects)
            pivot = fixed_framing["pivot"] if fixed_framing else pivot_for_item(self.context, item, objects, bounds)
            if self.settings.direction_strategy == "ROTATE_TARGET":
                rotate_objects(objects, pivot, direction.angle)
                bounds = object_bounds(objects)
            camera_bounds = fixed_framing["bounds"] if fixed_framing else bounds
            if self.settings.bake_mode == "CAMERA":
                camera = self.settings.bake_camera or self.scene.camera
                if camera is None or camera.type != "CAMERA":
                    raise RuntimeError("相机烘焙需要一个烘焙相机。")
                self.scene.camera = camera
                if direction.angle:
                    rotate_objects([camera], pivot, direction.angle)
                scale = camera.data.ortho_scale if camera.data.type == "ORTHO" else 0.0
            else:
                if self.settings.camera_source == "VISIBLE_BAKE_CAMERA":
                    camera = make_visible_bake_camera(self.scene, self.settings)
                else:
                    camera = make_camera(self.scene, self.settings)
                _, scale = configure_camera(self.scene, camera, self.settings, camera_bounds, direction.angle)

            for pass_id in enabled_passes(self.settings):
                self.configure_color_management_for_pass(pass_id)
                filepath = self.output_path(output_root, item, action_name, direction, output_frame or frame, pass_id, preview)
                filepath.parent.mkdir(parents=True, exist_ok=True)
                with self.pass_materials(objects, pass_id):
                    self.render_pass(filepath, pass_id)
                if pass_id == "NORMAL" and self.settings.normal_map_edge_padding:
                    expand_transparent_edge(filepath)
                files.append(str(filepath.relative_to(output_root)))

            self._last_frame_size = self.frame_size
            self._last_pivot_px = tuple(size // 2 for size in self.frame_size)
            self._last_scale = scale
            return files
        finally:
            state.restore()
            if self.settings.enable_pixel_bake and not is_supersampled(self.settings):
                remove_viewport_pixel_preview(self.scene)
            remove_temp_data()

    def pass_materials(self, objects, pass_id):
        if pass_id == "ALBEDO":
            return albedo_materials(objects)
        if pass_id == "NORMAL":
            return normal_materials(
                objects, unity_2d=self.settings.unity_2d_normal_map, pack_mask=packs_normal_mask(self.settings),
            )
        return mask_materials(objects)

    def configure_scene_for_render(self, objects):
        try:
            self.scene.render.engine = "BLENDER_EEVEE_NEXT"
        except TypeError:
            self.scene.render.engine = "BLENDER_EEVEE"
        width, height = self.frame_size
        self.scene.render.resolution_x = width * self.sample_factor
        self.scene.render.resolution_y = height * self.sample_factor
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
        if is_supersampled(self.settings):
            # Use the unscaled render; the selected algorithm owns downsampling.
            self.scene.render.use_compositing = False
            return
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

    def render_pass(self, filepath, pass_id):
        render = self.scene.render
        palette_options = self.palette_options if pass_id == "ALBEDO" else None
        needs_processing = self.sample_factor > 1 or palette_options is not None
        packed_normal = pass_id == "NORMAL" and packs_normal_mask(self.settings)
        previous_dither = render.dither_intensity
        if needs_processing or packed_normal:
            render.dither_intensity = 0.0
        try:
            if not needs_processing:
                render.filepath = str(filepath)
                bpy.ops.render.render(write_still=True)
                return

            with TemporaryDirectory(prefix="sbk_", dir=filepath.parent) as temp_dir:
                source = Path(temp_dir) / "source.png"
                destination = Path(temp_dir) / "processed.png"
                render.filepath = str(source)
                bpy.ops.render.render(write_still=True)
                process_render(
                    source, destination, self.frame_size, self.sample_factor, pass_id,
                    self.settings.pixel_downsample_method, palette_options,
                )
                destination.replace(filepath)
        finally:
            render.dither_intensity = previous_dither

    def configure_color_management_for_pass(self, pass_id):
        # Normal maps are vector data, not display colors. Writing them through
        # Standard/sRGB turns a neutral 0.5 component into about 0.735, which
        # Unity then decodes as a strongly biased normal direction.
        self.scene.view_settings.view_transform = "Raw" if pass_id == "NORMAL" else "Standard"
        self.scene.view_settings.look = "None"
        self.scene.view_settings.exposure = 0.0
        self.scene.view_settings.gamma = 1.0

    def apply_action(self, item, action):
        target = self.animation_target_for_item(item)
        if target is None or action is None:
            return
        target.animation_data_create()
        target.animation_data.action = action

    def animation_target_for_item(self, item):
        if self.settings.bake_mode == "CAMERA":
            return self.settings.camera_animation_target
        return item.armature or item.target_object

    def fixed_framing_for_action(self, item, action, directions, frame_jobs):
        if self.settings.bake_mode != "BATCH" or self.settings.batch_framing_mode != "LOCK_ACTION":
            return None

        objects = target_objects(item)
        armature = item.armature
        state_objects = list({obj for obj in objects + ([armature] if armature else []) if obj})
        state = SceneState(self.scene, state_objects)
        base_points = []
        rotated_points = []
        try:
            for source_frame, _output_frame in frame_jobs:
                state.restore()
                self.apply_action(item, action)
                self.scene.frame_set(source_frame)
                self.context.view_layer.update()
                base_bounds = object_bounds(objects)
                base_points.extend((base_bounds["min"].copy(), base_bounds["max"].copy()))

            if not base_points:
                return None

            base_bounds = bounds_from_points(base_points)
            fixed_pivot = pivot_for_item(self.context, item, objects, base_bounds)

            for source_frame, _output_frame in frame_jobs:
                for direction in directions:
                    state.restore()
                    self.apply_action(item, action)
                    self.scene.frame_set(source_frame)
                    self.context.view_layer.update()
                    if self.settings.direction_strategy == "ROTATE_TARGET":
                        rotate_objects(objects, fixed_pivot, direction.angle)
                        self.context.view_layer.update()
                    bounds = object_bounds(objects)
                    rotated_points.extend((bounds["min"].copy(), bounds["max"].copy()))

            if not rotated_points:
                return None
            return {"bounds": bounds_from_points(rotated_points), "pivot": fixed_pivot}
        finally:
            state.restore()

    def action_jobs(self, item):
        if self.settings.bake_mode == "CAMERA":
            start = self.settings.frame_start
            end = max(start, self.settings.frame_end)
            action = self.settings.camera_action
            action_name = action.name if action is not None else "Camera"
            return [(action_name, action, start, end)]
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

    def write_atlases(self, output_root, item, action_name, frames):
        if not self.settings.merge_atlas:
            return []

        atlas_files = []
        for direction_name in sorted({entry["direction"] for entry in frames}):
            direction_frames = [entry for entry in frames if entry["direction"] == direction_name]
            for pass_id, pass_label in PASS_LABELS.items():
                pass_files = [
                    Path(file)
                    for entry in direction_frames
                    for file in entry["pass_files"]
                    if len(Path(file).parts) >= 2 and Path(file).parts[-2] == pass_label
                ]
                if not pass_files:
                    continue
                source_paths = [output_root / file for file in pass_files]
                atlas_name = f"{slugify(item.name)}_{slugify(action_name)}_{slugify(direction_name)}_{pass_label}_Atlas.png"
                atlas_path = output_root / slugify(item.name) / slugify(action_name) / slugify(direction_name) / pass_label / atlas_name
                atlas_info = build_sprite_atlas(source_paths, atlas_path)
                if atlas_info is None:
                    continue
                atlas_info["file"] = str(atlas_path.relative_to(output_root))
                atlas_info["pass"] = pass_label
                atlas_info["direction"] = direction_name
                atlas_files.append(atlas_info)
        return atlas_files

    def write_metadata(self, output_root, item, action_name, frames, atlas_files=None):
        action_root = output_root / slugify(item.name) / slugify(action_name)
        action_root.mkdir(parents=True, exist_ok=True)
        data = {
            "frame_size": list(self.frame_size),
            "frame_count": max((entry["frame"] for entry in frames), default=0),
            "pivot_px": [size // 2 for size in self.frame_size],
            "pixels_per_unit": self.settings.pixels_per_unit,
            "item": item.name,
            "action": action_name,
            "directions": frames,
            "atlas_files": atlas_files or [],
        }
        if packs_normal_mask(self.settings):
            data["normal_map_encoding"] = "XY_MASK_R"
        with (action_root / "metadata.json").open("w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=2, ensure_ascii=False)


def bounds_from_points(points):
    min_v = Vector((min(p.x for p in points), min(p.y for p in points), min(p.z for p in points)))
    max_v = Vector((max(p.x for p in points), max(p.y for p in points), max(p.z for p in points)))
    return {"min": min_v, "max": max_v}


def ensure_directions(item):
    if item.directions:
        return
    if not hasattr(item.directions, "clear"):
        return
    from .operators import generate_directions_for_item

    generate_directions_for_item(item)


class CameraExportItem:
    armature = None
    animation_mode = "STATIC"
    actions = ()
    use_action_frame_range = False
    pivot_mode = "AUTO"
    custom_pivot = (0.0, 0.0, 0.0)

    def __init__(self, context, source_item=None):
        self.context = context
        settings = context.scene.sprite_baker_settings
        self.name = source_item.name if source_item else "Camera"
        self.target_type = source_item.target_type if source_item else "SCENE"
        self.target_object = source_item.target_object if source_item else None
        self.target_collection = source_item.target_collection if source_item else None
        self.frame_start = settings.frame_start
        self.frame_end = settings.frame_end
        self.direction_preset = settings.direction_preset
        self.custom_directions = settings.custom_directions
        self.directions = settings.directions
        self.active_direction_index = settings.active_direction_index
