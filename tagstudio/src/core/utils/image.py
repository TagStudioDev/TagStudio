# Copyright (C) 2024 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio

from PIL import Image
import numpy as np


def replace_transparent_pixels(
    img: Image.Image, color: tuple[int, int, int, int] = (255, 255, 255, 255)
) -> Image.Image:
    """
    Replaces (copying/without mutating) all transparent pixels in an image with the color.

    Args:
        img (Image.Image):
            The source image
        color (tuple[int, int, int, int]):
            The color (RGBA, 0 to 255) which transparent pixels should be set to.
            Defaults to white (255, 255, 255, 255)

    Returns:
        Image.Image:
            A copy of img with the pixels replaced.
    """
    pixel_array = np.asarray(img.convert("RGBA")).copy()
    pixel_array[pixel_array[:, :, 3] == 0] = color
    return Image.fromarray(pixel_array)
