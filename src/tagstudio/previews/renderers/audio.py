# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


import math
from io import BytesIO
from pathlib import Path
from typing import override
from warnings import catch_warnings

import numpy as np
import structlog
from mutagen import flac, id3, mp4
from mutagen._util import MutagenError
from PIL import ImageDraw
from PIL.Image import Image, Resampling
from PIL.Image import new as new_image
from PIL.Image import open as open_image

from tagstudio.core.enums import Theme
from tagstudio.core.media_types import MediaTypes
from tagstudio.previews.base_preview import RENDER, BasePreview
from tagstudio.previews.effects import apply_overlay_color
from tagstudio.previews.vendored.pydub.audio_segment import (
    _AudioSegment as AudioSegment,  # pyright: ignore[reportPrivateUsage]
)
from tagstudio.qt.views.styles.palette import UiColor

logger = structlog.get_logger(__name__)

MediaTypes.register("audio", ".aac", RENDER)
MediaTypes.register("audio", ".aif", RENDER)
MediaTypes.register("audio", ".aifc", RENDER)
MediaTypes.register("audio", ".caf", RENDER)
MediaTypes.register("audio", ".flac", RENDER)
MediaTypes.register("audio", ".m4a", RENDER)
MediaTypes.register("audio", ".m4p", RENDER)
MediaTypes.register("audio", ".mp3", RENDER)
MediaTypes.register("audio", ".ogg", RENDER)
MediaTypes.register("audio", ".wav", RENDER)
MediaTypes.register("audio", ".wma", RENDER)


class AudioPreview(BasePreview):
    media_type_name = "audio"
    priority = 70

    @override
    @classmethod
    def render(
        cls,
        filepath: Path,
        is_small: bool,
        theme: Theme,
        size: tuple[int, int],
        dpi_scale: float,
    ) -> Image | None:

        return cls.audio_album_thumb(filepath) or cls.audio_waveform_thumb(
            filepath, theme, size, dpi_scale
        )

    @staticmethod
    def audio_album_thumb(filepath: Path) -> Image | None:
        """Return an album cover thumb from an audio file if a cover is present.

        Args:
            filepath (Path): The path of the file.
        """
        image: Image | None = None
        ext = filepath.suffix.lower()
        try:
            if not filepath.is_file():
                raise FileNotFoundError

            artwork = None
            if ext in {".mp3", ".aif", ".aiff"}:
                id3_tags: id3.ID3 = id3.ID3(filepath)
                id3_covers: list = id3_tags.getall("APIC")  # pyright: ignore[reportUnknownVariableType]
                if id3_covers:
                    artwork = open_image(BytesIO(id3_covers[0].data))
            elif ext in {".flac"}:
                flac_tags: flac.FLAC = flac.FLAC(filepath)
                flac_covers: list = flac_tags.pictures  # pyright: ignore[reportUnknownVariableType]
                if flac_covers:
                    artwork = open_image(BytesIO(flac_covers[0].data))
            elif ext in {".mp4", ".m4a", ".aac", ".alac"}:
                mp4_tags: mp4.MP4 = mp4.MP4(filepath)
                mp4_covers: list | None = mp4_tags.get("covr")  # pyright: ignore[reportUnknownVariableType]
                if mp4_covers:
                    artwork = open_image(BytesIO(mp4_covers[0]))
            if artwork:
                image = artwork
        except (
            FileNotFoundError,
            id3.ID3NoHeaderError,
            mp4.MP4MetadataError,
            mp4.MP4StreamInfoError,
            MutagenError,
        ) as e:
            logger.error("Couldn't read album artwork", path=filepath, error=type(e).__name__)
        return image

    @staticmethod
    def audio_waveform_thumb(
        filepath: Path, theme: Theme, size: tuple[int, int], dpi_scale: float
    ) -> Image | None:
        """Render a waveform image from an audio file.

        Args:
            filepath (Path): The path of the file.
            theme (Theme): The system color theme.
            size (int): The size of the thumbnail.
            dpi_scale (float): The screen pixel ratio.
        """
        # BASE_SCALE used for drawing on a larger image and resampling down
        # to provide an antialiased effect.
        base_scale: int = 2
        samples_per_bar: int = 3
        size_scaled: int = size[0] * base_scale  # TODO: Allow for non-square sizes
        allow_small_min: bool = False
        im: Image | None = None

        try:
            bar_count: int = min(math.floor((size[0] // dpi_scale) / 5), 64)
            audio = AudioSegment.from_file(filepath, filepath.suffix.lower()[1:])  # pyright: ignore[reportUnknownVariableType]
            data = np.frombuffer(buffer=audio._data, dtype=np.int16)
            data_indices = np.linspace(1, len(data), num=bar_count * samples_per_bar)
            bar_margin: float = ((size_scaled / (bar_count * 3)) * base_scale) / 2
            line_width: float = ((size_scaled - bar_margin) / (bar_count * 3)) * base_scale
            bar_height: float = (size_scaled) - (size_scaled // bar_margin)

            count: int = 0
            maximum_item: int = 0
            max_array: list[int] = []
            highest_line: int = 0

            for i in range(-1, len(data_indices)):
                d = data[math.ceil(data_indices[i]) - 1]
                if count < samples_per_bar:
                    count = count + 1
                    with catch_warnings(record=True):
                        if abs(d) > maximum_item:
                            maximum_item = int(abs(d))
                else:
                    max_array.append(maximum_item)

                    if maximum_item > highest_line:
                        highest_line = maximum_item

                    maximum_item = 0
                    count = 1

            line_ratio = max(highest_line / bar_height, 1)

            im = new_image("RGB", (size_scaled, size_scaled), color="#000000")
            draw = ImageDraw.Draw(im)

            current_x = bar_margin
            for item in max_array:
                item_height = item / line_ratio

                # If small minimums are not allowed, raise all values
                # smaller than the line width to the same value.
                if not allow_small_min:
                    item_height = max(item_height, line_width)

                current_y = (bar_height - item_height + (size_scaled // bar_margin)) // 2

                draw.rounded_rectangle(
                    (
                        current_x,
                        current_y,
                        (current_x + line_width),
                        (current_y + item_height),
                    ),
                    radius=100 * base_scale,
                    fill=("#FF0000"),
                    outline=("#FFFF00"),
                    width=max(math.ceil(line_width / 6), base_scale),
                )

                current_x = current_x + line_width + bar_margin

            im.resize(size, Resampling.BILINEAR)
            im = apply_overlay_color(im, UiColor.GREEN, theme)

        except Exception as e:
            logger.error("Couldn't render waveform", path=filepath.name, error=type(e).__name__)

        return im
