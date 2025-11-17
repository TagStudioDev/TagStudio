from enum import Enum

from tagstudio.core.media_types import MediaCategories
from tagstudio.qt.previews.renderers.base_renderer import BaseRenderer
from tagstudio.qt.previews.renderers.ebook_renderer import EBookRenderer
from tagstudio.qt.previews.renderers.krita_renderer import KritaRenderer
from tagstudio.qt.previews.renderers.video_renderer import VideoRenderer


class RendererType(Enum):
    EBOOK = "ebook", MediaCategories.EBOOK_TYPES, EBookRenderer
    KRITA = "krita", MediaCategories.KRITA_TYPES, KritaRenderer
    VIDEO = "video", MediaCategories.VIDEO_TYPES, VideoRenderer

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
