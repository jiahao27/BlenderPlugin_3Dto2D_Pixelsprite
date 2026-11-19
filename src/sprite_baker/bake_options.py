MAX_SUPERSAMPLE_PIXELS = 4096 ** 2


def output_size(settings):
    if settings.enable_pixel_bake and settings.pixel_canvas_preset != "CUSTOM":
        size = int(settings.pixel_canvas_preset)
        return size, size
    return settings.resolution_x, settings.resolution_y


def is_supersampled(settings):
    return settings.enable_pixel_bake and settings.pixel_sampling == "SUPERSAMPLE"


def supersample_factor(settings):
    return settings.pixel_sample_factor if is_supersampled(settings) else 1


def packs_normal_mask(settings):
    return settings.use_normal and settings.pack_mask_in_normal and not is_supersampled(settings)


def enabled_passes(settings):
    passes = []
    if settings.use_albedo:
        passes.append("ALBEDO")
    if settings.use_normal:
        passes.append("NORMAL")
    if settings.use_mask and not is_supersampled(settings):
        passes.append("MASK")
    return passes
