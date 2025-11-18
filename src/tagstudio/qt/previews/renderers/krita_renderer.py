import zipfile
from io import BytesIO

import structlog
from PIL import Image

from tagstudio.qt.previews.renderers.base_renderer import BaseRenderer, RendererContext

logger = structlog.get_logger(__name__)

thumbnail_path_within_zip: str = "preview.png"


class KritaRenderer(BaseRenderer):
    def __init__(self):
        super().__init__()

    @staticmethod
    def render(context: RendererContext) -> Image.Image | None:
        """Extract and render a thumbnail for a Krita file.

        Args:
            context (RendererContext): The renderer context.
        """
        try:
            with zipfile.ZipFile(context.path, "r") as zip_file:
                # Check if the file exists in the zip
                if thumbnail_path_within_zip in zip_file.namelist():
                    # Read the specific file into memory
                    file_data: bytes = zip_file.read(thumbnail_path_within_zip)
                    embedded_thumbnail: Image.Image = Image.open(BytesIO(file_data))

                    if embedded_thumbnail:
                        rendered_image = Image.new("RGB", embedded_thumbnail.size, color="#1e1e1e")
                        rendered_image.paste(embedded_thumbnail)
                        return rendered_image
                else:
                    raise FileNotFoundError
        except Exception as e:
            logger.error("[KritaRenderer] Couldn't render thumbnail", path=context.path, error=e)

        return None
