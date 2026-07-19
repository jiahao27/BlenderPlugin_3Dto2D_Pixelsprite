import bpy


GRID_IMAGE_PREFIX = "SBK 像素网格"
GRID_TEXTURE_MAX_SIZE = 1024


def _grid_image_name(width, height):
    return f"{GRID_IMAGE_PREFIX} {width}x{height}"


def _grid_image_dimensions(width, height):
    scale = max(1, min(GRID_TEXTURE_MAX_SIZE // width, GRID_TEXTURE_MAX_SIZE // height))
    return width * scale, height * scale, scale


def get_or_create_grid_image(width, height):
    name = _grid_image_name(width, height)
    image_width, image_height, cell_size = _grid_image_dimensions(width, height)
    image = bpy.data.images.get(name)

    if image is not None and tuple(image.size) == (image_width, image_height):
        return image
    if image is None:
        image = bpy.data.images.new(name=name, width=image_width, height=image_height, alpha=True)
    else:
        image.scale(image_width, image_height)

    pixels = [0.0] * (image_width * image_height * 4)
    for y in range(image_height):
        for x in range(image_width):
            is_line = x % cell_size == 0 or y % cell_size == 0
            is_border = x == image_width - 1 or y == image_height - 1
            if not is_line and not is_border:
                continue
            index = (y * image_width + x) * 4
            pixels[index:index + 4] = (1.0, 1.0, 1.0, 0.7 if is_border else 0.4)
    image.pixels.foreach_set(pixels)
    image.pack()
    return image


def attach_grid_background(camera_data, width, height, opacity):
    image = get_or_create_grid_image(width, height)
    camera_data.show_background_images = True
    while len(camera_data.background_images) > 0:
        camera_data.background_images.remove(camera_data.background_images[0])
    background = camera_data.background_images.new()
    background.image = image
    background.alpha = opacity
    background.frame_method = "FIT"
    if hasattr(background, "display_depth"):
        background.display_depth = "FRONT"
    return image


def clear_grid_backgrounds():
    cleared_count = 0
    for camera in bpy.data.cameras:
        for background in list(camera.background_images):
            if background.image is None or not background.image.name.startswith(GRID_IMAGE_PREFIX):
                continue
            background.image = None
            camera.background_images.remove(background)
            cleared_count += 1
        if len(camera.background_images) == 0:
            camera.show_background_images = False
        camera.update_tag()
    return cleared_count


def set_grid_background_opacity(opacity):
    updated_count = 0
    for camera in bpy.data.cameras:
        for background in camera.background_images:
            if background.image is None or not background.image.name.startswith(GRID_IMAGE_PREFIX):
                continue
            background.alpha = opacity
            updated_count += 1
    return updated_count
