"""Run the Sprite Baker image algorithm tests with any Python that has NumPy."""

import sys
import unittest
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from sprite_baker.image_processing import downsample_rgba, parse_palette, quantize_rgba


class ImageProcessingTests(unittest.TestCase):
    def test_center_top_left_and_mode_pick_different_representatives(self):
        block = np.full((3, 3, 4), (0, 255, 0, 255), dtype=np.uint8)
        block[0, 0] = [255, 0, 0, 255]
        block[1, 1] = [0, 0, 255, 255]
        expected = {
            "CENTER": [0, 0, 255, 255],
            "TOP_LEFT": [255, 0, 0, 255],
            "MODE": [0, 255, 0, 255],
        }
        for method, value in expected.items():
            with self.subTest(method=method):
                np.testing.assert_array_equal(downsample_rgba(block, 3, method)[0, 0], value)

    def test_transparent_colors_do_not_pollute_visible_samples(self):
        block = np.full((2, 2, 4), (0, 255, 0, 0), dtype=np.uint8)
        block[1, 1] = [255, 0, 0, 255]
        for method in ("CENTER", "TOP_LEFT", "AVERAGE", "MODE"):
            with self.subTest(method=method):
                np.testing.assert_array_equal(downsample_rgba(block, 2, method)[0, 0], [255, 0, 0, 64])

    def test_color_average_operates_in_linear_light(self):
        block = np.full((2, 2, 4), (0, 0, 0, 255), dtype=np.uint8)
        block[1, :, :3] = 255
        np.testing.assert_array_equal(downsample_rgba(block, 2, "AVERAGE")[0, 0], [188, 188, 188, 255])

    def test_normal_average_is_renormalized(self):
        block = np.full((2, 2, 4), (255, 128, 128, 255), dtype=np.uint8)
        block[1] = [128, 128, 255, 255]
        result = downsample_rgba(block, 2, "NORMAL")[0, 0]
        normal = result[:3] / 127.5 - 1
        np.testing.assert_allclose(normal, [2 ** -0.5, 0, 2 ** -0.5], atol=0.008)
        self.assertAlmostEqual(np.linalg.norm(normal), 1.0, places=2)
        self.assertEqual(result[3], 255)

    def test_fixed_palette_keeps_alpha_and_transparent_pixels(self):
        palette = parse_palette("#FF0000，0000ff; #FF0000")
        pixels = np.asarray([[[230, 20, 0, 128], [20, 0, 240, 255], [13, 14, 15, 0]]], dtype=np.uint8)
        expected = [[[255, 0, 0, 128], [0, 0, 255, 255], [13, 14, 15, 0]]]
        np.testing.assert_array_equal(quantize_rgba(pixels, palette=palette), expected)
        with self.assertRaises(ValueError):
            parse_palette("#eee")

    def test_kmeans_uses_frequencies_and_repeats_with_seed(self):
        pixels = np.asarray([[
            [0, 0, 0, 255], [200, 0, 0, 255], [200, 0, 0, 255], [200, 0, 0, 255], [0, 255, 0, 0],
        ]], dtype=np.uint8)
        one = quantize_rgba(pixels, k=1)
        np.testing.assert_array_equal(one[0, :4, 0], [150, 150, 150, 150])
        np.testing.assert_array_equal(one[0, 4], pixels[0, 4])
        gradient = np.asarray([[[value, 0, 0, 255] for value in (0, 20, 40, 200, 220, 240)]], dtype=np.uint8)
        two = quantize_rgba(gradient, k=2, seed=7)
        np.testing.assert_array_equal(two, quantize_rgba(gradient, k=2, seed=7))
        np.testing.assert_array_equal(two[0, :, 0], [20, 20, 20, 220, 220, 220])


if __name__ == "__main__":
    unittest.main()
