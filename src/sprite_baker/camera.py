import math

import bpy
from mathutils import Matrix, Vector


def make_camera(scene, settings):
    data = bpy.data.cameras.new("SBK_TMP_camera")
    camera = bpy.data.objects.new("SBK_TMP_camera", data)
    scene.collection.objects.link(camera)
    data.type = "ORTHO" if settings.camera_mode == "ORTHO" else "PERSP"
    data.lens = 80
    scene.camera = camera
    return camera


def make_visible_bake_camera(scene, settings):
    camera = settings.bake_camera
    if camera is None or camera.name not in bpy.data.objects:
        data = bpy.data.cameras.new("SBK 可见烘焙相机")
        camera = bpy.data.objects.new("SBK 可见烘焙相机", data)
        scene.collection.objects.link(camera)
        settings.bake_camera = camera
    camera.data.type = "ORTHO" if settings.camera_mode == "ORTHO" else "PERSP"
    camera.data.lens = 80
    scene.camera = camera
    return camera


def look_at(camera, target):
    direction = Vector(target) - camera.location
    camera.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def configure_camera(scene, camera, settings, bounds, angle_deg=0.0):
    center = (bounds["min"] + bounds["max"]) * 0.5
    size = bounds["max"] - bounds["min"]
    horizontal = max(size.x, 0.01)
    vertical = max(size.z, 0.01)
    scale = max(horizontal * settings.resolution_y / settings.resolution_x, vertical)
    scale *= 1.0 + settings.margin
    distance = max(scale * 4.0, 10.0)

    if settings.direction_strategy == "CAMERA_ORBIT":
        radians = math.radians(angle_deg)
        offset = Vector((math.sin(radians) * distance, -math.cos(radians) * distance, 0.0))
    else:
        offset = Vector((0.0, -distance, 0.0))

    camera.location = center + offset
    look_at(camera, center)
    if camera.data.type == "ORTHO":
        camera.data.ortho_scale = scale
    else:
        camera.data.lens = 80

    return center, scale


def object_bounds(objects):
    points = []
    depsgraph = bpy.context.evaluated_depsgraph_get()
    for obj in objects:
        if obj.type != "MESH":
            continue
        evaluated = obj.evaluated_get(depsgraph)
        for corner in evaluated.bound_box:
            points.append(evaluated.matrix_world @ Vector(corner))
    if not points:
        return {"min": Vector((-0.5, -0.5, -0.5)), "max": Vector((0.5, 0.5, 0.5))}
    min_v = Vector((min(p.x for p in points), min(p.y for p in points), min(p.z for p in points)))
    max_v = Vector((max(p.x for p in points), max(p.y for p in points), max(p.z for p in points)))
    return {"min": min_v, "max": max_v}


def pivot_for_item(context, item, objects, bounds):
    if item.pivot_mode == "ORIGIN" and item.target_object:
        return item.target_object.matrix_world.translation.copy()
    if item.pivot_mode == "CURSOR":
        return context.scene.cursor.location.copy()
    if item.pivot_mode == "CUSTOM":
        return Vector(item.custom_pivot)
    return (bounds["min"] + bounds["max"]) * 0.5


def rotate_objects(objects, pivot, angle_deg):
    matrix = (
        Matrix.Translation(pivot)
        @ Matrix.Rotation(math.radians(angle_deg), 4, "Z")
        @ Matrix.Translation(-pivot)
    )
    for obj in objects:
        obj.matrix_world = matrix @ obj.matrix_world
