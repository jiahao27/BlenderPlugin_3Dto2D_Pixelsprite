"""Sprite image algorithms on top-down, straight-alpha uint8 RGBA arrays."""

import re

import numpy as np


def downsample_rgba(pixels, factor, method):
    """Reduce integer-sized blocks; alpha always represents area coverage."""
    height, width = pixels.shape[:2]
    if factor < 1 or height % factor or width % factor:
        raise ValueError("图像尺寸必须是降采样倍数的整数倍。")
    if method not in {"CENTER", "TOP_LEFT", "AVERAGE", "MODE", "NORMAL"}:
        raise ValueError(f"未知的像素采样算法：{method}")

    out_height, out_width = height // factor, width // factor
    result = np.empty((out_height, out_width, 4), dtype=np.uint8)
    rows_per_batch = max(1, 262144 // (width * factor))
    for start in range(0, out_height, rows_per_batch):
        end = min(start + rows_per_batch, out_height)
        block_rows = pixels[start * factor:end * factor]
        blocks = block_rows.reshape(end - start, factor, out_width, factor, 4)
        blocks = blocks.transpose(0, 2, 1, 3, 4).reshape(-1, factor * factor, 4)
        alpha = blocks[..., 3]
        coverage = np.rint(alpha.mean(axis=1)).astype(np.uint8)

        if method in {"CENTER", "TOP_LEFT"}:
            rgb = representative_rgb(blocks, factor, method)
        elif method == "MODE":
            rgb = mode_rgb(blocks)
        elif method == "AVERAGE":
            linear = srgb_to_linear(blocks[..., :3].astype(np.float32) / 255)
            total = alpha.sum(axis=1)[:, None]
            mean = (linear * alpha[..., None]).sum(axis=1) / np.maximum(total, 1)
            rgb = byte_values(linear_to_srgb(mean))
        else:
            vectors = blocks[..., :3].astype(np.float32) / 127.5 - 1.0
            total = alpha.sum(axis=1)[:, None]
            mean = (vectors * alpha[..., None]).sum(axis=1) / np.maximum(total, 1)
            # Opposing directions can cancel. Use a visible sample in that case.
            degenerate = (np.linalg.norm(mean, axis=1) < 0.01) & (total[:, 0] > 0)
            if np.any(degenerate):
                fallback = representative_rgb(blocks[degenerate], factor, "CENTER")
                mean[degenerate] = fallback.astype(np.float32) / 127.5 - 1.0
            length = np.linalg.norm(mean, axis=1, keepdims=True)
            rgb = byte_values((mean / np.maximum(length, 1e-8)) * 0.5 + 0.5)

        rgb[coverage == 0] = 0
        target = result[start:end].reshape(-1, 4)
        target[:, :3] = rgb
        target[:, 3] = coverage
    return result


def representative_rgb(blocks, factor, method):
    indices = np.arange(factor * factor)
    y, x = divmod(indices, factor)
    anchor = (factor - 1) / 2 if method == "CENTER" else 0
    order = np.argsort((x - anchor) ** 2 + (y - anchor) ** 2, kind="stable")
    # If the preferred sample is transparent, choose the nearest visible one.
    positions = order[np.argmax(blocks[:, order, 3] > 0, axis=1)]
    return blocks[np.arange(len(blocks)), positions, :3]


def mode_rgb(blocks):
    # Count exact visible RGB values. For equal counts choose the smallest RGB key.
    sentinel = 1 << 24
    keys = np.sort(np.where(blocks[..., 3] > 0, rgb_keys(blocks[..., :3]), sentinel), axis=1)
    best = keys[:, 0].copy()
    best_count = np.zeros(len(keys), dtype=np.int32)
    count = np.zeros_like(best_count)
    previous = np.full_like(best, sentinel)
    for key in keys.T:
        count = np.where(key == previous, count + 1, 1)
        replace = (key != sentinel) & (count > best_count)
        best[replace] = key[replace]
        best_count[replace] = count[replace]
        previous = key
    return rgb_from_keys(best)


def srgb_to_linear(values):
    return np.where(values <= 0.04045, values / 12.92, ((values + 0.055) / 1.055) ** 2.4)


def linear_to_srgb(values):
    return np.where(values <= 0.0031308, values * 12.92, 1.055 * values ** (1 / 2.4) - 0.055)


def byte_values(values):
    return np.rint(np.clip(values, 0, 1) * 255).astype(np.uint8)


def rgb_keys(rgb):
    return (rgb[..., 0].astype(np.uint32) << 16) | (rgb[..., 1].astype(np.uint32) << 8) | rgb[..., 2]


def rgb_from_keys(keys):
    return np.stack(((keys >> 16) & 255, (keys >> 8) & 255, keys & 255), axis=-1).astype(np.uint8)


def parse_palette(text):
    entries = re.split(r"[\s,，;；]+", text.strip())
    if not all(re.fullmatch(r"#?[0-9a-fA-F]{6}", entry) for entry in entries):
        raise ValueError("请填写六位 HEX 颜色，例如 #202030, #E8AA73。")
    keys = list(dict.fromkeys(int(entry.lstrip("#"), 16) for entry in entries))
    if len(keys) > 256:
        raise ValueError("固定调色板最多支持 256 种颜色。")
    return rgb_from_keys(np.asarray(keys, dtype=np.uint32))


def nearest_colors(colors, palette):
    colors = colors.astype(np.float32, copy=False)
    palette = palette.astype(np.float32, copy=False)
    labels = np.empty(len(colors), dtype=np.int32)
    batch_size = max(1, 262144 // len(palette))
    for start in range(0, len(colors), batch_size):
        batch = colors[start:start + batch_size]
        diff = batch[:, None, :] - palette
        distances = np.einsum("nki,nki->nk", diff, diff)
        labels[start:start + len(batch)] = distances.argmin(axis=1)
    return labels


def kmeans_palette(colors, counts, k, max_iterations, seed):
    """Standard RGB Lloyd iterations. The histogram counts equal repeated samples."""
    if len(colors) <= k:
        return colors.copy()
    rng = np.random.default_rng(seed)
    centers = colors[rng.choice(len(colors), size=k, replace=False)].astype(np.float32)
    for _ in range(max_iterations):
        labels = nearest_colors(colors, centers)
        weights = np.bincount(labels, weights=counts, minlength=k)
        populated = weights > 0
        updated = centers.copy()
        for channel in range(3):
            sums = np.bincount(labels, weights=counts * colors[:, channel], minlength=k)
            updated[populated, channel] = sums[populated] / weights[populated]
        if np.array_equal(centers, updated):
            break
        centers = updated
    return np.rint(centers).astype(np.uint8)


def quantize_rgba(pixels, *, palette=None, k=16, max_iterations=20, seed=0):
    """Fit a palette per image, or apply user colors without moving them."""
    visible = pixels[..., 3] > 0
    result = pixels.copy()
    if not np.any(visible):
        return result

    colors, inverse, counts = np.unique(
        rgb_keys(pixels[visible, :3]), return_inverse=True, return_counts=True,
    )
    colors = rgb_from_keys(colors)
    if palette is None:
        palette = kmeans_palette(colors, counts, k, max_iterations, seed)
    result[visible, :3] = palette[nearest_colors(colors, palette)[inverse]]
    return result
