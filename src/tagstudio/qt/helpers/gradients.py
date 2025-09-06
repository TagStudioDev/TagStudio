# Copyright (C) 2024 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio


from PIL import Image


def four_corner_gradient(
    image: Image.Image, size: tuple[int, int], mask: Image.Image | None = None
) -> Image.Image:
    if image.size != size:
        # Four-Corner Gradient Background.
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
        if mask:
            final.paste(bg, mask=mask.getchannel(0))
        else:
            final = bg

    else:
        final = Image.new("RGBA", size, (0, 0, 0, 0))
        if mask:
            final.paste(image, mask=mask.getchannel(0))
        else:
            final = image

    if final.mode != "RGBA":
        final = final.convert("RGBA")

    return final


def linear_gradient(
    size: tuple[int, int],
    colors: list[str],
    interpolation: Image.Resampling = Image.Resampling.BICUBIC,
) -> Image.Image:
    seed: Image.Image = Image.new(mode="RGBA", size=(len(colors), 1), color="#000000")
    for i, color in enumerate(colors):
        c_im: Image.Image = Image.new(mode="RGBA", size=(1, 1), color=color)
        seed.paste(c_im, (i, 0))
    gradient: Image.Image = seed.resize(size, resample=interpolation)
    return gradient
