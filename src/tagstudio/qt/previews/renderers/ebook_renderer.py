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
    def __init__(self):
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

            # Get the cover from the comic metadata, if present
            if "ComicInfo.xml" in archive.get_name_list():
                comic_info = ElementTree.fromstring(archive.read("ComicInfo.xml"))
                rendered_image = EBookRenderer.__cover_from_comic_info(
                    archive, comic_info, "FrontCover"
                )
                if not rendered_image:
                    rendered_image = EBookRenderer.__cover_from_comic_info(
                        archive, comic_info, "InnerCover"
                    )

            # Get the first image present
            if not rendered_image:
                for file_name in archive.get_name_list():
                    if file_name.lower().endswith(
                        (".png", ".jpg", ".jpeg", ".gif", ".bmp", ".svg")
                    ):
                        image_data = archive.read(file_name)
                        rendered_image = Image.open(BytesIO(image_data))
                        break

            return rendered_image
        except Exception as e:
            logger.error("[EBookRenderer] Couldn't render thumbnail", path=context.path, error=e)

        return None

    @staticmethod
    def __cover_from_comic_info(
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
        cover = comic_info.find(f"./*Page[@Type='{cover_type}']")
        if cover is not None:
            pages = [
                page_file for page_file in archive.get_name_list() if page_file != "ComicInfo.xml"
            ]
            page_name = pages[int(unwrap(cover.get("Image")))]
            if page_name.endswith((".png", ".jpg", ".jpeg", ".gif", ".bmp", ".svg")):
                image_data = archive.read(page_name)
                return Image.open(BytesIO(image_data))

        return None
