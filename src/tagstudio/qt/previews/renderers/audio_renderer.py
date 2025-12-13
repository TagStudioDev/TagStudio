import math
from io import BytesIO
from warnings import catch_warnings

import numpy as np
import structlog
from mutagen import flac, id3, mp4
from PIL import (
    Image,
    ImageDraw,
)
from pydub import AudioSegment

from tagstudio.qt.helpers.image_effects import apply_overlay_color
from tagstudio.qt.models.palette import UiColor
from tagstudio.qt.previews.renderers.base_renderer import BaseRenderer, RendererContext

logger = structlog.get_logger(__name__)


class AudioRenderer(BaseRenderer):
    def __init__(self) -> None:
        super().__init__()

    @staticmethod
    def render(context: RendererContext) -> Image.Image | None:
        """Render a thumbnail for an audio file.

        Args:
            context (RendererContext): The renderer context.
        """
        rendered_image: Image.Image | None = _extract_album_cover(context)

        if rendered_image is None:
            rendered_image = _render_audio_waveform(context)
            if rendered_image is not None:
                rendered_image = apply_overlay_color(rendered_image, UiColor.GREEN)

        return rendered_image


def _extract_album_cover(context: RendererContext) -> Image.Image | None:
    """Return an album cover thumb from an audio file if a cover is present.

    Args:
        context (RendererContext): The renderer context.
    """
    try:
        if not context.path.is_file():
            raise FileNotFoundError

        artwork: Image.Image | None = None

        # Get cover from .mp3 tags
        if context.extension in [".mp3"]:
            id3_tags: id3.ID3 = id3.ID3(context.path)
            id3_covers: list = id3_tags.getall("APIC")
            if id3_covers:
                artwork = Image.open(BytesIO(id3_covers[0].data))

        # Get cover from .flac tags
        elif context.extension in [".flac"]:
            flac_tags: flac.FLAC = flac.FLAC(context.path)
            flac_covers: list = flac_tags.pictures
            if flac_covers:
                artwork = Image.open(BytesIO(flac_covers[0].data))

        # Get cover from .mp4 tags
        elif context.extension in [".mp4", ".m4a", ".aac"]:
            mp4_tags: mp4.MP4 = mp4.MP4(context.path)
            mp4_covers: list | None = mp4_tags.get("covr")  # pyright: ignore[reportAssignmentType]
            if mp4_covers:
                artwork = Image.open(BytesIO(mp4_covers[0]))

        return artwork
    except Exception as e:
        logger.error("[AudioRenderer] Couldn't read album artwork", path=context.path, error=e)

    return None


def _render_audio_waveform(context: RendererContext) -> Image.Image | None:
    """Render a waveform image from an audio file.

    Args:
        context (RendererContext): The renderer context.
    """
    # BASE_SCALE used for drawing on a larger image and resampling down
    # to provide an antialiased effect.
    base_scale: int = 2
    samples_per_bar: int = 3
    size_scaled: int = context.size * base_scale
    allow_small_min: bool = False

    try:
        bar_count: int = min(math.floor((context.size // context.pixel_ratio) / 5), 64)
        audio = AudioSegment.from_file(context.path, context.extension[1:])
        data = np.frombuffer(buffer=audio._data, dtype=np.int16)
        data_indices = np.linspace(1, len(data), num=bar_count * samples_per_bar)
        bar_margin: float = ((size_scaled / (bar_count * 3)) * base_scale) / 2
        line_width: float = ((size_scaled - bar_margin) / (bar_count * 3)) * base_scale
        bar_height: float = size_scaled - (size_scaled // bar_margin)

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

        rendered_image = Image.new("RGB", (size_scaled, size_scaled), color="#000000")
        draw = ImageDraw.Draw(rendered_image)

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
                fill="#FF0000",
                outline="#FFFF00",
                width=max(math.ceil(line_width / 6), base_scale),
            )

            current_x = current_x + line_width + bar_margin

        rendered_image.resize((context.size, context.size), Image.Resampling.BILINEAR)
        return rendered_image

    except Exception as e:
        logger.error("[AudioRenderer] Couldn't render waveform", path=context.path.name, error=e)

    return None
