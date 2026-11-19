"""Blender PNG I/O adapter for the independent image algorithms."""

import bpy
import numpy as np

from .image_processing import byte_values, downsample_rgba, quantize_rgba


def process_render(source, destination, size, factor, pass_id, sampling_method, palette_options):
    image = bpy.data.images.load(str(source), check_existing=False)
    try:
        image.colorspace_settings.name = "Non-Color"
        image.alpha_mode = "STRAIGHT"
        width, height = image.size
        if (width, height) != (size[0] * factor, size[1] * factor):
            raise RuntimeError(f"渲染尺寸不符合采样设置：{width} × {height}。")
        rgba = np.empty((height, width, 4), dtype=np.float32)
        image.pixels.foreach_get(rgba.ravel())
        # Blender's first image row is the bottom row. The algorithm uses top-down rows.
        pixels = byte_values(rgba[::-1])
    finally:
        bpy.data.images.remove(image)

    if factor > 1:
        method = "NORMAL" if pass_id == "NORMAL" else sampling_method
        pixels = downsample_rgba(pixels, factor, method)
    if palette_options is not None:
        pixels = quantize_rgba(pixels, **palette_options)

    image = bpy.data.images.new("SBK Processed Frame", width=size[0], height=size[1], alpha=True)
    try:
        image.colorspace_settings.name = "Non-Color" if pass_id == "NORMAL" else "sRGB"
        image.alpha_mode = "STRAIGHT"
        image.pixels.foreach_set(np.ascontiguousarray(pixels[::-1], dtype=np.float32).ravel() / np.float32(255))
        image.filepath_raw = str(destination)
        image.file_format = "PNG"
        image.save()
    finally:
        bpy.data.images.remove(image)
