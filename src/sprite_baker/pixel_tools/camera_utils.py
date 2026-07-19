import math


def get_camera_type(settings, camera_object):
    if camera_object.name.startswith("SBK 等距"):
        return "ISO"
    if camera_object.name.startswith("SBK 正面"):
        return "PIXEL"
    return settings.pixel_camera_type


def apply_camera_transform(camera_object, camera_type, distance):
    if camera_type == "ISO":
        camera_object.location = (distance, -distance, distance)
        camera_object.rotation_euler = (math.radians(54.7356), 0.0, math.radians(45.0))
        return
    camera_object.location = (0.0, -distance, 0.0)
    camera_object.rotation_euler = (math.radians(90.0), 0.0, 0.0)


def apply_camera_projection(camera_object, projection, ortho_scale):
    camera_object.data.type = projection
    if projection == "ORTHO":
        camera_object.data.ortho_scale = ortho_scale
