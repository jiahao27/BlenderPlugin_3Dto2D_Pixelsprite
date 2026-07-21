import bpy


def expand_transparent_edge(filepath, alpha_threshold=0.001):
    """Copy normal RGB values one pixel past an opaque sprite silhouette.

    The added pixels remain fully transparent. This prevents bilinear texture
    filtering from mixing a sprite edge with the transparent PNG background.
    """
    image = bpy.data.images.load(str(filepath), check_existing=False)
    try:
        image.colorspace_settings.name = "Non-Color"
        width, height = image.size
        if width < 2 or height < 2:
            return False

        source = list(image.pixels[:])
        result = source[:]
        changed = False
        neighbors = (
            (-1, -1), (0, -1), (1, -1),
            (-1, 0),           (1, 0),
            (-1, 1),  (0, 1),  (1, 1),
        )

        for y in range(height):
            for x in range(width):
                index = (y * width + x) * 4
                if source[index + 3] > alpha_threshold:
                    continue

                for offset_x, offset_y in neighbors:
                    source_x = x + offset_x
                    source_y = y + offset_y
                    if not (0 <= source_x < width and 0 <= source_y < height):
                        continue
                    source_index = (source_y * width + source_x) * 4
                    if source[source_index + 3] <= alpha_threshold:
                        continue
                    result[index:index + 3] = source[source_index:source_index + 3]
                    changed = True
                    break

        if not changed:
            return False

        image.pixels[:] = result
        image.filepath_raw = str(filepath)
        image.file_format = "PNG"
        image.save()
        return True
    finally:
        bpy.data.images.remove(image)
