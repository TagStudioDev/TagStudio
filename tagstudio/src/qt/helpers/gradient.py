# Copyright (C) 2024 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio

from PIL import Image, ImageEnhance, ImageChops


def four_corner_gradient_background(image: Image.Image, adj_size, mask, hl):
    if image.size != (adj_size, adj_size):
        # Old 1 color method.
        # bg_col = image.copy().resize((1, 1)).getpixel((0,0))
        # bg = Image.new(mode='RGB',size=(adj_size,adj_size),color=bg_col)
        # bg.thumbnail((1, 1))
        # bg = bg.resize((adj_size,adj_size), resample=Image.Resampling.NEAREST)

        # Small gradient background. Looks decent, and is only a one-liner.
        # bg = image.copy().resize((2, 2), resample=Image.Resampling.BILINEAR).resize((adj_size,adj_size),resample=Image.Resampling.BILINEAR)

        # Four-Corner Gradient Background.
        # Not exactly a one-liner, but it's (subjectively) really cool.
        tl = image.getpixel((0, 0))
        tr = image.getpixel(((image.size[0] - 1), 0))
        bl = image.getpixel((0, (image.size[1] - 1)))
        br = image.getpixel(((image.size[0] - 1), (image.size[1] - 1)))
        bg = Image.new(mode="RGB", size=(2, 2))
        bg.paste(tl, (0, 0, 2, 2))
        bg.paste(tr, (1, 0, 2, 2))
        bg.paste(bl, (0, 1, 2, 2))
        bg.paste(br, (1, 1, 2, 2))
        bg = bg.resize((adj_size, adj_size), resample=Image.Resampling.BICUBIC)

        bg.paste(
            image,
            box=(
                (adj_size - image.size[0]) // 2,
                (adj_size - image.size[1]) // 2,
            ),
        )

        bg.putalpha(mask)
        final = bg

    else:
        image.putalpha(mask)
        final = image

    hl_soft = hl.copy()
    hl_soft.putalpha(ImageEnhance.Brightness(hl.getchannel(3)).enhance(0.5))
    final.paste(ImageChops.soft_light(final, hl_soft), mask=hl_soft.getchannel(3))
    return final
