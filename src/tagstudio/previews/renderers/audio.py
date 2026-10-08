# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: MIT


from io import BytesIO
from pathlib import Path
from typing import override

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


class AudioPreview(BasePreview):
    media_type_name = "audio"
    priority = 70

    @override
    @classmethod
    def register_types(cls) -> None:
        # NOTE: Filetype equivalents (i.e. ".aif" == ".aif") are already declared internally.
        MediaTypes.register("audio", ".aac", RENDER)
        MediaTypes.register("audio", ".aif", RENDER)
        MediaTypes.register("audio", ".aifc", RENDER)
        MediaTypes.register("audio", ".caf", RENDER)
        MediaTypes.register("audio", ".flac", RENDER)
        MediaTypes.register("audio", ".m4a", RENDER)
        MediaTypes.register("audio", ".m4p", RENDER)
        MediaTypes.register("audio", ".m4r", RENDER)
        MediaTypes.register("audio", ".mp3", RENDER)
        MediaTypes.register("audio", ".ogg", RENDER)
        MediaTypes.register("audio", ".wav", RENDER)
        MediaTypes.register("audio", ".wma", RENDER)

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

        return cls.audio_album_thumb(filepath) or cls.audio_waveform_thumb(filepath, theme, size)

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
    def audio_waveform_thumb(filepath: Path, theme: Theme, size: tuple[int, int]) -> Image | None:
        """Render a waveform image from an audio file.

        Args:
            filepath (Path): The path of the file.
            theme (Theme): The system color theme.
            size (int): The size of the thumbnail.
        """
        # BASE_SCALE used for drawing on a larger image and resampling down
        # to provide an antialiased effect.
        base_scale: int = 2
        size_scaled: int = size[0] * base_scale  # TODO: Allow for non-square sizes
        allow_small_min: bool = False
        im: Image | None = None

        try:
            bar_count: int = 32
            audio = AudioSegment.from_file(filepath, filepath.suffix.lower()[1:])  # pyright: ignore[reportUnknownVariableType]
            data = np.frombuffer(buffer=audio._data, dtype=f"<i{audio.sample_width}")
            # Bars are twice as wide as the gaps between them, with double gaps at the edges
            bar_margin: float = size_scaled / (bar_count * 3 + 3)
            line_width: float = bar_margin * 2
            bar_height: float = size_scaled * 0.7

            # Each bar shows the RMS-adjusted waveforms of its section of the audio.
            # RMS waveforms display nicer than raw ones, especially for loud files.
            chunks = np.array_split(data, bar_count)
            levels: list[float] = [
                float(np.sqrt(np.mean(np.square(c, dtype=np.float64)))) for c in chunks
            ]
            line_ratio = max(*levels, 1) / bar_height

            im = new_image("RGB", (size_scaled, size_scaled), color="#000000")
            draw = ImageDraw.Draw(im)

            current_x = bar_margin * 2
            for item in levels:
                item_height = item / line_ratio

                # If small minimums are not allowed, raise all values
                # smaller than the line width to the same value.
                if not allow_small_min:
                    item_height = max(item_height, line_width)

                current_y = (size_scaled - item_height) // 2

                draw.rounded_rectangle(
                    (
                        current_x,
                        current_y,
                        (current_x + line_width),
                        (current_y + item_height),
                    ),
                    radius=100 * base_scale,
                    fill=("#FF0000"),
                )

                current_x = current_x + line_width + bar_margin

            im.resize(size, Resampling.BILINEAR)
            im = apply_overlay_color(im, UiColor.GREEN, theme)

        except Exception as e:
            logger.error("Couldn't render waveform", path=filepath.name, error=type(e).__name__)

        return im
