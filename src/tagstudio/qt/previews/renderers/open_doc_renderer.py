from io import BytesIO

import structlog
from PIL import (
    Image,
)

from tagstudio.qt.helpers.file_wrappers.archive.zip_file import ZipFile
from tagstudio.qt.previews.renderers.base_renderer import BaseRenderer, RendererContext

logger = structlog.get_logger(__name__)


thumbnail_path_within_zip: str = "Thumbnails/thumbnail.png"


class OpenDocRenderer(BaseRenderer):
    def __init__(self) -> None:
        super().__init__()

    @staticmethod
    def render(context: RendererContext) -> Image.Image | None:
        """Render a thumbnail for an OpenDocument file.

        Args:
            context (RendererContext): The renderer context.
        """
        try:
            zip_file: ZipFile
            with ZipFile(context.path, "r") as zip_file:
                # Check if the file exists in the zip
                if zip_file.has_file_name(thumbnail_path_within_zip):
                    # Read the specific file into memory
                    file_data: bytes | None = zip_file.read(thumbnail_path_within_zip)
                    if file_data is None:
                        raise OSError

                    embedded_thumbnail: Image.Image = Image.open(BytesIO(file_data))

                    if embedded_thumbnail:
                        rendered_image = Image.new("RGB", embedded_thumbnail.size, color="#1e1e1e")
                        rendered_image.paste(embedded_thumbnail)
                        return rendered_image
                else:
                    raise FileNotFoundError
        except Exception as e:
            logger.error("[OpenDocRenderer] Couldn't render thumbnail", path=context.path, error=e)

        return None
