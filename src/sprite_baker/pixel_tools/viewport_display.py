def set_render_preview_pixel_size(scene):
    render_settings = getattr(scene, "render", None)
    if render_settings is None or not hasattr(render_settings, "preview_pixel_size"):
        return False
    try:
        render_settings.preview_pixel_size = "1"
    except TypeError:
        return False
    return True


def set_viewport_render_preview(context, rendered=False):
    screen = getattr(context, "screen", None)
    if screen is None:
        return 0

    updated_count = 0
    for area in screen.areas:
        if area.type != "VIEW_3D":
            continue
        for space in area.spaces:
            if space.type != "VIEW_3D" or not hasattr(space, "shading"):
                continue
            shading = space.shading
            if hasattr(shading, "use_compositor"):
                try:
                    shading.use_compositor = "CAMERA"
                except TypeError:
                    pass
            if rendered and hasattr(shading, "type"):
                try:
                    shading.type = "RENDERED"
                except TypeError:
                    pass
            updated_count += 1
            area.tag_redraw()
    return updated_count


def viewport_render_preview_is_ready(context, rendered=False):
    screen = getattr(context, "screen", None)
    if screen is None:
        return True

    found_viewport = False
    for area in screen.areas:
        if area.type != "VIEW_3D":
            continue
        for space in area.spaces:
            if space.type != "VIEW_3D" or not hasattr(space, "shading"):
                continue
            found_viewport = True
            shading = space.shading
            if hasattr(shading, "use_compositor") and shading.use_compositor != "CAMERA":
                return False
            if rendered and hasattr(shading, "type") and shading.type != "RENDERED":
                return False
    return True if found_viewport else True
