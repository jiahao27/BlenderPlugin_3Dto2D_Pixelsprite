import math
from pathlib import Path

import bpy


def is_prime(value):
    if value <= 1:
        return False
    if value == 2:
        return True
    if value % 2 == 0:
        return False
    limit = int(math.sqrt(value))
    for divisor in range(3, limit + 1, 2):
        if value % divisor == 0:
            return False
    return True


def atlas_grid(frame_count):
    if frame_count <= 0 or is_prime(frame_count):
        return None
    root = int(math.sqrt(frame_count))
    if root * root == frame_count:
        return root, root
    for rows in range(root, 1, -1):
        if frame_count % rows == 0:
            return frame_count // rows, rows
    return None


def build_sprite_atlas(source_paths, output_path):
    grid = atlas_grid(len(source_paths))
    if grid is None:
        return None
    columns, rows = grid
    images = []
    atlas_image = None
    try:
        for source_path in source_paths:
            image = bpy.data.images.load(str(source_path), check_existing=False)
            set_non_color(image)
            images.append(image)

        tile_width, tile_height = images[0].size
        for image in images:
            if tuple(image.size) != (tile_width, tile_height):
                raise RuntimeError("图集合并要求同一组序列帧尺寸一致。")

        atlas_width = tile_width * columns
        atlas_height = tile_height * rows
        atlas_pixels = [0.0] * (atlas_width * atlas_height * 4)

        for index, image in enumerate(images):
            source_pixels = [0.0] * (tile_width * tile_height * 4)
            image.pixels.foreach_get(source_pixels)
            column = index % columns
            row = index // columns
            dst_x = column * tile_width
            dst_y = (rows - row - 1) * tile_height
            paste_pixels(source_pixels, atlas_pixels, tile_width, tile_height, atlas_width, dst_x, dst_y)

        atlas_image = bpy.data.images.new(
            name=Path(output_path).stem,
            width=atlas_width,
            height=atlas_height,
            alpha=True,
            float_buffer=False,
        )
        set_non_color(atlas_image)
        atlas_image.pixels.foreach_set(atlas_pixels)
        atlas_image.filepath_raw = str(output_path)
        atlas_image.file_format = "PNG"
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        atlas_image.save()
        return {
            "file": str(output_path),
            "columns": columns,
            "rows": rows,
            "frame_count": len(source_paths),
            "frame_size": [tile_width, tile_height],
            "atlas_size": [atlas_width, atlas_height],
        }
    finally:
        for image in images:
            if image.name in bpy.data.images:
                bpy.data.images.remove(image)
        if atlas_image is not None and atlas_image.name in bpy.data.images:
            bpy.data.images.remove(atlas_image)


def paste_pixels(source_pixels, atlas_pixels, tile_width, tile_height, atlas_width, dst_x, dst_y):
    for y in range(tile_height):
        for x in range(tile_width):
            source_index = (y * tile_width + x) * 4
            atlas_index = ((dst_y + y) * atlas_width + dst_x + x) * 4
            atlas_pixels[atlas_index:atlas_index + 4] = source_pixels[source_index:source_index + 4]


def set_non_color(image):
    try:
        image.colorspace_settings.name = "Non-Color"
    except TypeError:
        pass
