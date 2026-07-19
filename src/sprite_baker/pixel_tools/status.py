DEFAULT_STATUS_MESSAGE = "像素工具已就绪。"


def set_status(context, message):
    scene = getattr(context, "scene", None)
    if scene is None or not hasattr(scene, "sprite_baker_pixel_tools"):
        return
    scene.sprite_baker_pixel_tools.status_message = message
