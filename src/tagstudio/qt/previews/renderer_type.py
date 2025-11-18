from enum import Enum

from tagstudio.core.media_types import MediaCategories
from tagstudio.qt.previews.renderers.audio_renderer import AudioRenderer
from tagstudio.qt.previews.renderers.base_renderer import BaseRenderer
from tagstudio.qt.previews.renderers.ebook_renderer import EBookRenderer
from tagstudio.qt.previews.renderers.font_renderer import FontRenderer
from tagstudio.qt.previews.renderers.krita_renderer import KritaRenderer
from tagstudio.qt.previews.renderers.text_renderer import TextRenderer
from tagstudio.qt.previews.renderers.video_renderer import VideoRenderer
from tagstudio.qt.previews.renderers.vtf_renderer import VTFRenderer


class RendererType(Enum):
    EBOOK = "ebook", MediaCategories.EBOOK_TYPES, EBookRenderer

    VTF = "vtf", MediaCategories.SOURCE_ENGINE_TYPES, VTFRenderer

    # Project files
    KRITA = "krita", MediaCategories.KRITA_TYPES, KritaRenderer

    VIDEO = "video", MediaCategories.VIDEO_TYPES, VideoRenderer
    AUDIO = "audio", MediaCategories.AUDIO_TYPES, AudioRenderer

    TEXT = "text", MediaCategories.PLAINTEXT_TYPES, TextRenderer
    FONT = "font", MediaCategories.FONT_TYPES, FontRenderer

    def __init__(self, name: str, media_category: MediaCategories, renderer: type[BaseRenderer]):
        self.__name: str = name
        self.media_category: MediaCategories = media_category
        self.renderer: type[BaseRenderer] = renderer

    @staticmethod
    def get_renderer_type(file_extension: str) -> "RendererType | None":
        for renderer_type in RendererType.__members__.values():
            if MediaCategories.is_ext_in_category(
                file_extension, renderer_type.media_category, mime_fallback=True
            ):
                return renderer_type

        return None
