# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: MIT


import hashlib
import importlib
import inspect
import math
import pkgutil
from pathlib import Path
from typing import NamedTuple

import structlog
from PIL import Image, ImageFile

from tagstudio.core.enums import Theme
from tagstudio.core.library.alchemy.library import Library
from tagstudio.core.library.ignore import Ignore
from tagstudio.core.media_types import MediaTypes
from tagstudio.core.query_lang.file_groups import SEARCH
from tagstudio.core.utils.decompression import decompressed, get_inner_ext, is_compressed
from tagstudio.previews.base_preview import RENDER, BasePreview
from tagstudio.qt.app_settings import (
    DEFAULT_CACHED_THUMB_RES,
    MAX_CACHED_THUMB_RES,
    MIN_CACHED_THUMB_RES,
    AppSettings,
)
from tagstudio.qt.cache_manager import CacheManager

ImageFile.LOAD_TRUNCATED_IMAGES = True
Image.MAX_IMAGE_PIXELS = None


logger = structlog.get_logger(__name__)


# TODO: Allow user-created preview renderers from an external directory.
def _get_preview_renderers() -> list[type[BasePreview]]:
    """Discover all BasePreview subclasses in src/tagstudio/previews/renderers.

    Classes are sorted by their priority (descending), falling back to alphabetical order.
    """
    found: list[type[BasePreview]] = []
    from tagstudio.previews import renderers  # pyright: ignore

    for module_info in sorted(pkgutil.iter_modules(renderers.__path__), key=lambda m: m.name):
        module = importlib.import_module(f"{renderers.__name__}.{module_info.name}")
        for _, obj in inspect.getmembers(module, inspect.isclass):
            if (
                issubclass(obj, BasePreview)
                and obj is not BasePreview
                and obj.__module__ == module.__name__
            ):
                obj.register_types()
                if getattr(MediaTypes, obj.media_type_name, None) is None:
                    logger.error(
                        "[FileRenderer] Preview Renderer's media type isn't registered",
                        name=obj.__name__,
                        media_type=obj.media_type_name,
                    )
                else:
                    found.append(obj)
                break

    found.sort(key=lambda cls: cls.priority, reverse=True)
    for renderer in found:
        logger.info(
            "[FileRenderer] Loaded Preview Renderer",
            name=renderer.__name__,
            media_type=renderer.media_type_name,
            priority=renderer.priority,
        )
    return found


class RenderResult(NamedTuple):
    """A rendered image from a file with any statuses associated with it."""

    image: Image.Image | None
    is_ignored: bool = False
    is_unlinked: bool = False


class FileRenderer:
    """A class for rendering preview images and thumbnails from files."""

    _cached_img_ext: str = ".webp"
    _failed_render_filenames: set[Path] = set()  # Used to skip loading icon for default icon files
    _preview_renderers: list[type[BasePreview]] = _get_preview_renderers()

    # Map of media group keys to preview renderer priorities.
    _media_group_priorities: dict[str, int] = {
        renderer.media_type_name: renderer.priority for renderer in _preview_renderers
    }

    def __init__(self, library: Library, settings: AppSettings) -> None:
        self.lib = library
        self.settings = settings

    @classmethod
    def media_groups(cls, filepath: Path) -> list[str]:
        """Return the keys of the media groups a file belongs to, most specific first."""
        ext = get_inner_ext(filepath) or MediaTypes.get_ext(filepath)
        renderer = cls.find_renderer(filepath)
        groups = MediaTypes.find(ext, SEARCH)  # Fallback icons use the SEARCH context
        groups.sort(  # Most specific first, then the group that renders it, then by priority
            key=lambda g: (
                g.key.count("."),
                renderer is not None and g.key == renderer.media_type_name,
                cls._media_group_priorities.get(g.key, BasePreview.priority),
            ),
            reverse=True,
        )
        return [group.key for group in groups]

    @staticmethod
    def find_renderer(filepath: Path) -> type[BasePreview] | None:
        """Return the preview renderer for a file, or for the file inside it if it's compressed."""
        renderer = FileRenderer._find_renderer(filepath)
        if renderer is None and is_compressed(filepath):
            renderer = FileRenderer._find_renderer(Path(filepath.stem))
        return renderer

    @staticmethod
    def previously_failed(filepath: Path, theme: Theme, date_modified: float | None = None) -> bool:
        """Return whether rendering a file failed before."""
        file_name = FileRenderer._cached_thumb_name(filepath, theme, date_modified)
        return file_name in FileRenderer._failed_render_filenames

    @staticmethod
    def cached_thumbnail(
        cache: CacheManager | None,
        filepath: Path,
        theme: Theme,
        date_modified: float | None = None,
    ) -> Image.Image | None:
        """Return a file's cached thumbnail, if it has one."""
        if not cache:
            return None
        file_name = FileRenderer._cached_thumb_name(filepath, theme, date_modified)
        cached_path = cache.get_file_path(file_name)
        if not (cached_path and cached_path.is_file()):
            return None
        try:
            return Image.open(cached_path)
        except Exception as e:
            logger.error(
                "[FileRenderer] Couldn't open cached thumbnail!", path=cached_path, error=e
            )
            return None

    @staticmethod
    def _cached_thumb_name(
        filepath: Path, theme: Theme, date_modified: float | None = None
    ) -> Path:
        """Return the cache filename for a file's thumbnail.

        Args:
            filepath (Path): The path of the file to check for a cached image of.
            theme (Theme): The light/dark theme, used if the file's renderer has theme variants.
            date_modified (float | None): The file's stored date modified timestamp, if it has one.
        """
        mod_time: str = "" if date_modified is None else str(date_modified)
        renderer = FileRenderer.find_renderer(filepath)
        theme_name = theme.name if renderer is not None and renderer.has_theme_variants else ""
        hashable_str: str = f"{str(filepath)}{mod_time}{theme_name}"
        hash_value = hashlib.shake_128(hashable_str.encode("utf-8")).hexdigest(8)
        return Path(f"{hash_value}{FileRenderer._cached_img_ext}")

    def render(
        self,
        cache: CacheManager | None,
        filepath: Path | str,
        size: tuple[int, int],
        dpi_scale: float,
        theme: Theme = Theme.DARK,
        is_thumb: bool = False,
        date_modified: float | None = None,
    ) -> RenderResult:
        """Render a thumbnail or preview image of a file.

        Args:
            cache (CacheManager | None): A cache manager instance.
            filepath (str | Path): The path of the file to render a thumbnail for.
            size (tuple[int, int]): The unmodified base size of the thumbnail.
            dpi_scale (float): The screen pixel ratio.
            theme (Theme): A theme enum to determine the light/dark theme.
            is_thumb (bool): Is this specifically a thumbnail? Use for specifying small variants.
            date_modified (float | None): The date modified timestamp of the file. Used for caches.
        """
        if isinstance(filepath, str):
            filepath = Path(filepath)

        is_unlinked = not filepath.exists()
        is_ignored = False
        library_dir = self.lib.library_dir
        if library_dir is not None and filepath.is_relative_to(library_dir):
            is_ignored = Ignore.matcher.is_ignored(filepath.relative_to(library_dir))

        if is_thumb:
            image = self._get_thumbnail(cache, filepath, size, dpi_scale, theme, date_modified)
        else:
            image = self._render(filepath, size, dpi_scale, theme, date_modified)
            if image:
                image = image.convert("RGBA")
        return RenderResult(image, is_ignored, is_unlinked)

    def _get_thumbnail(
        self,
        cache: CacheManager | None,
        filepath: Path,
        size: tuple[int, int],
        dpi_scale: float,
        theme: Theme,
        date_modified: float | None,
    ) -> Image.Image | None:
        """Return a file's thumbnail from the cache, rendering and caching it first if needed.

        Args:
            cache (CacheManager | None): A cache manager instance.
            filepath (Path): The path of the file to render a thumbnail for.
            size (tuple[int, int]): The unmodified base size of the thumbnail.
            dpi_scale (float): The screen pixel ratio.
            theme (Theme): A theme enum to determine the light/dark theme.
            date_modified (float | None): The date modified timestamp of the file. Used for caches.
        """
        image = FileRenderer.cached_thumbnail(cache, filepath, theme, date_modified)
        if not image and self.settings.generate_thumbs:
            res = self.settings.cached_thumb_resolution
            if not MIN_CACHED_THUMB_RES <= res <= MAX_CACHED_THUMB_RES:
                res = DEFAULT_CACHED_THUMB_RES

            image = self._render(
                filepath, (res, res), 1, theme, date_modified, is_small=True, cache=cache
            )
        if not image:
            return None
        scaled_size = math.ceil(max(size) * dpi_scale)
        return self._resize_image(image, (scaled_size, scaled_size))

    def _render(
        self,
        filepath: Path,
        size: tuple[int, int],
        dpi_scale: float,
        theme: Theme,
        date_modified: float | None,
        is_small: bool = False,
        cache: CacheManager | None = None,
    ) -> Image.Image | None:
        """Render a file preview image.

        Args:
            filepath (Path): The path of the file to render.
            size (tuple[int, int]): The unmodified base size of the image.
            dpi_scale (float): The screen pixel ratio.
            theme (Theme): A theme enum to determine the light/dark theme.
            date_modified (float | None): The date modified timestamp of the file. Used for caches.
            is_small (bool): Is this specifically a thumbnail? Use for specifying small variants.
            cache (CacheManager | None): A cache manager to save the rendered image to, if any.
        """
        file_name = FileRenderer._cached_thumb_name(filepath, theme, date_modified)
        scaled_size = math.ceil(max(size) * dpi_scale)
        image: Image.Image | None = None

        if filepath.is_file():
            try:
                renderer = FileRenderer._find_renderer(filepath)
                if renderer:
                    image = renderer.render(
                        filepath=filepath,
                        is_small=is_small,
                        theme=theme,
                        size=(scaled_size, scaled_size),
                        dpi_scale=dpi_scale,
                    )
                elif is_compressed(filepath):
                    image = FileRenderer._render_decompressed(
                        filepath, is_small, theme, (scaled_size, scaled_size), dpi_scale
                    )

                if image:
                    image = self._resize_image(image, (scaled_size, scaled_size))
                if image and cache:
                    cache.save_image(image, file_name, mode="RGBA")
            except Exception as e:
                logger.error("[FileRenderer] Couldn't render thumbnail", filepath=filepath, error=e)
                image = None

        if image:
            FileRenderer._failed_render_filenames.discard(file_name)
        else:
            FileRenderer._failed_render_filenames.add(file_name)
        return image

    @staticmethod
    def _find_renderer(filepath: Path) -> type[BasePreview] | None:
        """Return the highest priority preview renderer for a file's extension, if any."""
        ext = MediaTypes.get_ext(filepath) if filepath.suffix else filepath.stem.lower()
        for renderer in FileRenderer._preview_renderers:
            if getattr(MediaTypes, renderer.media_type_name).contains(ext, RENDER):
                return renderer
        return None

    @staticmethod
    def _render_decompressed(
        filepath: Path, is_small: bool, theme: Theme, size: tuple[int, int], dpi_scale: float
    ) -> Image.Image | None:
        """Render a compressed file with the preview renderer for the uncompressed file."""
        preview = FileRenderer._find_renderer(Path(filepath.stem))
        if preview is None:
            return None

        with decompressed(filepath) as inner_path:
            if inner_path is None:
                return None

            image = preview.render(
                filepath=inner_path, is_small=is_small, theme=theme, size=size, dpi_scale=dpi_scale
            )
            if image:
                image.load()  # Read the image data before the temporary file is deleted
            return image

    @staticmethod
    def _resize_image(image: Image.Image, size: tuple[int, int]) -> Image.Image:
        orig_x, orig_y = image.size
        new_x, new_y = size

        if orig_x > orig_y:
            new_x = size[0]
            new_y = math.ceil(size[1] * (orig_y / orig_x))
        elif orig_y > orig_x:
            new_y = size[1]
            new_x = math.ceil(size[0] * (orig_x / orig_y))

        resampling_method = (
            Image.Resampling.NEAREST
            if max(image.size[0], image.size[1]) < max(size)
            else Image.Resampling.BILINEAR
        )
        image = image.resize((new_x, new_y), resample=resampling_method)

        return image
