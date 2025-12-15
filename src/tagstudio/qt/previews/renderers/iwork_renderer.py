from io import BytesIO

import structlog
from PIL import (
    Image,
)

from tagstudio.qt.helpers.file_wrappers.archive.zip_file import ZipFile
from tagstudio.qt.previews.renderers.base_renderer import BaseRenderer, RendererContext

logger = structlog.get_logger(__name__)


preview_thumbnail_path_within_zip: str = "preview.jpg"
quicklook_thumbnail_path_within_zip: str = "QuickLook/Thumbnail.jpg"


class IWorkRenderer(BaseRenderer):
    def __init__(self) -> None:
        super().__init__()

    @staticmethod
    def render(context: RendererContext) -> Image.Image | None:
        """Render a thumbnail for an Apple iWork (Pages, Numbers, Keynote) file.

        Args:
            context (RendererContext): The renderer context.
        """
        try:
            zip_file: ZipFile
            with ZipFile(context.path, "r") as zip_file:
                # Preview thumbnail
                if zip_file.has_file_name(preview_thumbnail_path_within_zip):
                    file_data: bytes | None = zip_file.read(preview_thumbnail_path_within_zip)
                    if file_data is None:
                        raise OSError

                    embedded_thumbnail: Image.Image = Image.open(BytesIO(file_data))

                # Quicklook thumbnail
                elif zip_file.has_file_name(quicklook_thumbnail_path_within_zip):
                    file_data = zip_file.read(quicklook_thumbnail_path_within_zip)
                    if file_data is None:
                        raise OSError

                    embedded_thumbnail = Image.open(BytesIO(file_data))
                else:
                    raise FileNotFoundError

                if embedded_thumbnail:
                    rendered_image = Image.new("RGB", embedded_thumbnail.size, color="#1e1e1e")
                    rendered_image.paste(embedded_thumbnail)
                    return rendered_image
        except Exception as e:
            logger.error("[IWorkRenderer] Couldn't render thumbnail", path=context.path, error=e)

        return None
