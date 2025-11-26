from io import BytesIO
from xml.etree import ElementTree
from xml.etree.ElementTree import Element

import structlog
from PIL import Image

from tagstudio.core.utils.types import unwrap
from tagstudio.qt.helpers.file_wrappers.archive.archive_file import ArchiveFile
from tagstudio.qt.helpers.file_wrappers.archive.rar_file import RarFile
from tagstudio.qt.helpers.file_wrappers.archive.seven_zip_file import SevenZipFile
from tagstudio.qt.helpers.file_wrappers.archive.tar_file import TarFile
from tagstudio.qt.helpers.file_wrappers.archive.zip_file import ZipFile
from tagstudio.qt.previews.renderers.base_renderer import BaseRenderer, RendererContext

logger = structlog.get_logger(__name__)


class EBookRenderer(BaseRenderer):
    def __init__(self) -> None:
        super().__init__()

    @staticmethod
    def render(context: RendererContext) -> Image.Image | None:
        """Extracts the cover specified by ComicInfo.xml or first image found in the ePub file.

        Args:
            context (RendererContext): The renderer context.

        Returns:
            Image: The cover specified in ComicInfo.xml,
            the first image found in the ePub file, or None by default.
        """
        try:
            archive: ArchiveFile | None = None
            match context.extension:
                case ".cb7":
                    archive = SevenZipFile(context.path, "r")
                case ".cbr":
                    archive = RarFile(context.path, "r")
                case ".cbt":
                    archive = TarFile(context.path, "r")
                case _:
                    archive = ZipFile(context.path, "r")

            rendered_image: Image.Image | None = None

            logger.debug("Epub")
            logger.debug(archive.get_name_list())

            # Get the cover from the comic metadata, if present
            if "ComicInfo.xml" in archive.get_name_list():
                logger.debug("Found ComicInfo.xml!")

                comic_info_bytes: bytes | None = archive.read("ComicInfo.xml")
                if comic_info_bytes is None:
                    raise OSError

                comic_info: Element = ElementTree.fromstring(comic_info_bytes.decode("utf-8"))
                logger.debug(comic_info)
                rendered_image = _extract_cover(archive, comic_info, "FrontCover")

                if not rendered_image:
                    rendered_image = _extract_cover(archive, comic_info, "InnerCover")

            # Get the first image present
            if not rendered_image:
                for file_name in archive.get_name_list():
                    if file_name.lower().endswith(
                        (".png", ".jpg", ".jpeg", ".gif", ".bmp", ".svg")
                    ):
                        image_data: bytes | None = archive.read(file_name)
                        if image_data is None:
                            raise OSError

                        rendered_image = Image.open(BytesIO(image_data))
                        break

            return rendered_image
        except Exception as e:
            logger.error("[EBookRenderer] Couldn't render thumbnail", path=context.path, error=e)

        return None


def _extract_cover(
    archive: ArchiveFile, comic_info: Element, cover_type: str
) -> Image.Image | None:
    """Extract the cover specified in ComicInfo.xml.

    Args:
        archive (ArchiveFile): The current ePub file.
        comic_info (Element): The parsed ComicInfo.xml.
        cover_type (str): The type of cover to load.

    Returns:
        Image: The cover specified in ComicInfo.xml.
    """
    cover: Element | None = comic_info.find(f"./*Page[@Type='{cover_type}']")
    if cover is not None:
        pages: list[str] = [
            page_file for page_file in archive.get_name_list() if page_file != "ComicInfo.xml"
        ]
        page_name: str = pages[int(unwrap(cover.get("Image")))]
        if page_name.endswith((".png", ".jpg", ".jpeg", ".gif", ".bmp", ".svg")):
            image_data: bytes | None = archive.read(page_name)
            if image_data is None:
                raise OSError

            return Image.open(BytesIO(image_data))

    return None
