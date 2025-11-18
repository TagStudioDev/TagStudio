from pathlib import Path

import srctools
import structlog
from PIL import Image

from tagstudio.qt.previews.renderers.base_renderer import BaseRenderer

logger = structlog.get_logger(__name__)


class VTFRenderer(BaseRenderer):
    def __init__(self):
        super().__init__()

    @staticmethod
    def render(path: Path, extension: str, size: int, is_grid_thumb: bool) -> Image.Image | None:
        """Extract and render a thumbnail for VTF (Valve Texture Format) images.

        Uses the srctools library for reading VTF files.

        Args:
            path (Path): The path of the file.
            extension (str): The file extension.
            size (tuple[int,int]): The size of the thumbnail.
            is_grid_thumb (bool): Whether the image will be used as a thumbnail in the file grid.
        """
        try:
            with open(path, "rb") as f:
                vtf = srctools.VTF.read(f)
                return vtf.get(frame=0).to_PIL()

        except (ValueError, FileNotFoundError) as e:
            logger.error("[VTFRenderer] Couldn't render thumbnail", path=path, error=e)

        return None
