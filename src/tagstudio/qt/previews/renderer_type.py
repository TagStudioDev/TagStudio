from enum import Enum

from tagstudio.core.media_types import MediaCategories
from tagstudio.qt.previews.renderers.audio_renderer import AudioRenderer
from tagstudio.qt.previews.renderers.base_renderer import BaseRenderer
from tagstudio.qt.previews.renderers.blender_renderer import BlenderRenderer
from tagstudio.qt.previews.renderers.ebook_renderer import EBookRenderer
from tagstudio.qt.previews.renderers.exr_image_renderer import EXRImageRenderer
from tagstudio.qt.previews.renderers.font_renderer import FontRenderer
from tagstudio.qt.previews.renderers.iwork_renderer import IWorkRenderer
from tagstudio.qt.previews.renderers.krita_renderer import KritaRenderer
from tagstudio.qt.previews.renderers.open_doc_renderer import OpenDocRenderer
from tagstudio.qt.previews.renderers.pdf_renderer import PDFRenderer
from tagstudio.qt.previews.renderers.powerpoint_renderer import PowerPointRenderer
from tagstudio.qt.previews.renderers.raster_image_renderer import RasterImageRenderer
from tagstudio.qt.previews.renderers.raw_image_renderer import RawImageRenderer
from tagstudio.qt.previews.renderers.text_renderer import TextRenderer
from tagstudio.qt.previews.renderers.vector_image_renderer import VectorImageRenderer
from tagstudio.qt.previews.renderers.video_renderer import VideoRenderer
from tagstudio.qt.previews.renderers.vtf_renderer import VTFRenderer


class RendererType(Enum):
    # Image files
    RASTER_IMAGE = "image", MediaCategories.IMAGE_RASTER_TYPES, RasterImageRenderer, True
    VECTOR_IMAGE = "vector_image", MediaCategories.IMAGE_VECTOR_TYPES, VectorImageRenderer, True
    EXR_IMAGE = "exr_image", MediaCategories.IMAGE_EXR_TYPES, EXRImageRenderer, True
    VTF = "vtf", MediaCategories.SOURCE_ENGINE_TYPES, VTFRenderer, True
    RAW_IMAGE = "raw_image", MediaCategories.IMAGE_RAW_TYPES, RawImageRenderer, True

    # Media files
    VIDEO = "video", MediaCategories.VIDEO_TYPES, VideoRenderer, True
    AUDIO = "audio", MediaCategories.AUDIO_TYPES, AudioRenderer, False

    # Project files
    KRITA = "krita", MediaCategories.KRITA_TYPES, KritaRenderer, True

    # Document files
    OPEN_DOC = "open_doc", MediaCategories.OPEN_DOCUMENT_TYPES, OpenDocRenderer, True
    POWERPOINT = "powerpoint", MediaCategories.POWERPOINT_TYPES, PowerPointRenderer, True
    PDF = "pdf", MediaCategories.PDF_TYPES, PDFRenderer, True
    IWORK = "iwork", MediaCategories.IWORK_TYPES, IWorkRenderer, True

    # eBook files
    EBOOK = "ebook", MediaCategories.EBOOK_TYPES, EBookRenderer, True

    # Model files
    BLENDER = "blender", MediaCategories.BLENDER_TYPES, BlenderRenderer, True

    # Font files
    FONT = "font", MediaCategories.FONT_TYPES, FontRenderer, True

    # Text files
    TEXT = "text", MediaCategories.PLAINTEXT_TYPES, TextRenderer, True

    def __init__(
        self,
        name: str,
        media_category: MediaCategories,
        renderer: type[BaseRenderer],
        is_savable_media_type: bool,
    ):
        self.__name: str = name
        self.media_category: MediaCategories = media_category
        self.renderer: type[BaseRenderer] = renderer

        self.is_savable_media_type = is_savable_media_type

    @staticmethod
    def get_renderer_type(file_extension: str) -> "RendererType | None":
        for renderer_type in RendererType.__members__.values():
            if MediaCategories.is_ext_in_category(
                file_extension, renderer_type.media_category, mime_fallback=True
            ):
                return renderer_type

        return None
