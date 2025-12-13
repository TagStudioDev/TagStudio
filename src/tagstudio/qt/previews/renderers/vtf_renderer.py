import srctools
import structlog
from PIL import Image

from tagstudio.qt.previews.renderers.base_renderer import BaseRenderer, RendererContext

logger = structlog.get_logger(__name__)


class VTFRenderer(BaseRenderer):
    def __init__(self) -> None:
        super().__init__()

    @staticmethod
    def render(context: RendererContext) -> Image.Image | None:
        """Extract and render a thumbnail for VTF (Valve Texture Format) images.

        Uses the srctools library for reading VTF files.

        Args:
            context (RendererContext): The renderer context.
        """
        try:
            with open(context.path, "rb") as vtf_file:
                vtf = srctools.VTF.read(vtf_file)
                return vtf.get(frame=0).to_PIL()

        except (ValueError, FileNotFoundError) as e:
            logger.error("[VTFRenderer] Couldn't render thumbnail", path=context.path, error=e)

        return None
