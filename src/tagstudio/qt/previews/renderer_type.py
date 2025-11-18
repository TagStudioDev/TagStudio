from enum import Enum

from tagstudio.core.media_types import MediaCategories
from tagstudio.qt.previews.renderers.audio_renderer import AudioRenderer
from tagstudio.qt.previews.renderers.base_renderer import BaseRenderer
from tagstudio.qt.previews.renderers.blender_renderer import BlenderRenderer
from tagstudio.qt.previews.renderers.ebook_renderer import EBookRenderer
from tagstudio.qt.previews.renderers.font_renderer import FontRenderer
from tagstudio.qt.previews.renderers.krita_renderer import KritaRenderer
from tagstudio.qt.previews.renderers.pdf_renderer import PDFRenderer
from tagstudio.qt.previews.renderers.powerpoint_renderer import PowerPointRenderer
from tagstudio.qt.previews.renderers.text_renderer import TextRenderer
from tagstudio.qt.previews.renderers.video_renderer import VideoRenderer
from tagstudio.qt.previews.renderers.vtf_renderer import VTFRenderer


class RendererType(Enum):
    # Project files
    KRITA = "krita", MediaCategories.KRITA_TYPES, KritaRenderer

    # Model files
    BLENDER = "blender", MediaCategories.BLENDER_TYPES, BlenderRenderer

    # Media files
    VIDEO = "video", MediaCategories.VIDEO_TYPES, VideoRenderer
    AUDIO = "audio", MediaCategories.AUDIO_TYPES, AudioRenderer

    # Document files
    POWERPOINT = "powerpoint", MediaCategories.POWERPOINT_TYPES, PowerPointRenderer
    PDF = "pdf", MediaCategories.PDF_TYPES, PDFRenderer
    EBOOK = "ebook", MediaCategories.EBOOK_TYPES, EBookRenderer

    # Text files
    TEXT = "text", MediaCategories.PLAINTEXT_TYPES, TextRenderer
    FONT = "font", MediaCategories.FONT_TYPES, FontRenderer

    # Image files
    VTF = "vtf", MediaCategories.SOURCE_ENGINE_TYPES, VTFRenderer

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
