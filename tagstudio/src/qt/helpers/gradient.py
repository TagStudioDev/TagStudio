# Copyright (C) 2024 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio

from PIL import Image


def four_corner_gradient(
    image: Image.Image, size: tuple[int, int], mask: Image.Image
) -> Image.Image:
    if image.size != size:
        # Old 1 color method.
        # bg_col = image.copy().resize((1, 1)).getpixel((0,0))
        # bg = Image.new(mode='RGB',size=size,color=bg_col)
        # bg.thumbnail((1, 1))
        # bg = bg.resize(size, resample=Image.Resampling.NEAREST)

        # Small gradient background. Looks decent, and is only a one-liner.
        # bg = image.copy().resize((2, 2), resample=Image.Resampling.BILINEAR).resize(size,resample=Image.Resampling.BILINEAR)

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
        bg = bg.resize(size, resample=Image.Resampling.BICUBIC)
        bg.paste(
            image,
            box=(
                (size[0] - image.size[0]) // 2,
                (size[1] - image.size[1]) // 2,
            ),
        )

        final = Image.new("RGBA", bg.size, (0, 0, 0, 0))
        final.paste(bg, mask=mask.getchannel(0))

        # bg.putalpha(mask)
        # final = bg

    else:
        # image.putalpha(mask)
        # final = image

        final = Image.new("RGBA", size, (0, 0, 0, 0))
        final.paste(image, mask=mask.getchannel(0))

    if final.mode != "RGBA":
        final = final.convert("RGBA")

    return final


def linear_gradient(
    size=tuple[int, int],
    colors=list[str],
    interpolation: Image.Resampling = Image.Resampling.BICUBIC,
) -> Image.Image:
    seed: Image.Image = Image.new(mode="RGBA", size=(len(colors), 1), color="#000000")
    for i, color in enumerate(colors):
        c_im: Image.Image = Image.new(mode="RGBA", size=(1, 1), color=color)
        seed.paste(c_im, (i, 0))
    gradient: Image.Image = seed.resize(size, resample=interpolation)
    return gradient
