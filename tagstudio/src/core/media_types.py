# Copyright (C) 2024 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio

import logging
import mimetypes
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

logging.basicConfig(format="%(message)s", level=logging.INFO)


class MediaType(str, Enum):
    """Names of media types."""

    ADOBE_PHOTOSHOP: str = "adobe_photoshop"
    AFFINITY_PHOTO: str = "affinity_photo"
    ARCHIVE: str = "archive"
    AUDIO_MIDI: str = "audio_midi"
    AUDIO: str = "audio"
    BLENDER: str = "blender"
    DATABASE: str = "database"
    DISK_IMAGE: str = "disk_image"
    DOCUMENT: str = "document"
    EBOOK: str = "ebook"
    FONT: str = "font"
    IMAGE_ANIMATED: str = "image_animated"
    IMAGE_RAW: str = "image_raw"
    IMAGE_VECTOR: str = "image_vector"
    IMAGE: str = "image"
    INSTALLER: str = "installer"
    MATERIAL: str = "material"
    MODEL: str = "model"
    OPEN_DOCUMENT: str = "open_document"
    PACKAGE: str = "package"
    PDF: str = "pdf"
    PLAINTEXT: str = "plaintext"
    PRESENTATION: str = "presentation"
    PROGRAM: str = "program"
    SHORTCUT: str = "shortcut"
    SOURCE_ENGINE: str = "source_engine"
    SPREADSHEET: str = "spreadsheet"
    TEXT: str = "text"
    VIDEO: str = "video"


@dataclass(frozen=True)
class MediaCategory:
    """An object representing a category of media.

    Includes a MediaType identifier, extensions set, and IANA status flag.

    Args:
        media_type (MediaType): The MediaType Enum representing this category.

        extensions (set[str]): The set of file extensions associated with this category.
            Includes leading ".", all lowercase, and does not need to be unique to this category.

        is_iana (bool): Represents whether or not this is an IANA registered category.
    """

    media_type: MediaType
    extensions: set[str]
    name: str
    is_iana: bool = False


class MediaCategories:
    """Contain pre-made MediaCategory objects as well as methods to interact with them."""

    # These sets are used either individually or together to form the final sets
    # for the MediaCategory(s).
    # These sets may be combined and are NOT 1:1 with the final categories.
    _ADOBE_PHOTOSHOP_SET: set[str] = {
        ".pdd",
        ".psb",
        ".psd",
    }
    _AFFINITY_PHOTO_SET: set[str] = {".afphoto"}
    _ARCHIVE_SET: set[str] = {
        ".7z",
        ".gz",
        ".rar",
        ".s7z",
        ".tar",
        ".tgz",
        ".zip",
    }
    _AUDIO_MIDI_SET: set[str] = {
        ".mid",
        ".midi",
    }
    _AUDIO_SET: set[str] = {
        ".aac",
        ".aif",
        ".aiff",
        ".alac",
        ".flac",
        ".m4a",
        ".m4p",
        ".mp3",
        ".mpeg4",
        ".ogg",
        ".wav",
        ".wma",
    }
    _BLENDER_SET: set[str] = {
        ".blen_tc",
        ".blend",
        ".blend1",
        ".blend2",
        ".blend3",
        ".blend4",
        ".blend5",
        ".blend6",
        ".blend7",
        ".blend8",
        ".blend9",
        ".blend10",
        ".blend11",
        ".blend12",
        ".blend13",
        ".blend14",
        ".blend15",
        ".blend16",
        ".blend17",
        ".blend18",
        ".blend19",
        ".blend20",
        ".blend21",
        ".blend22",
        ".blend23",
        ".blend24",
        ".blend25",
        ".blend26",
        ".blend27",
        ".blend28",
        ".blend29",
        ".blend30",
        ".blend31",
        ".blend32",
    }
    _DATABASE_SET: set[str] = {
        ".accdb",
        ".mdb",
        ".sqlite",
        ".sqlite3",
    }
    _DISK_IMAGE_SET: set[str] = {".bios", ".dmg", ".iso"}
    _DOCUMENT_SET: set[str] = {
        ".doc",
        ".docm",
        ".docx",
        ".dot",
        ".dotm",
        ".dotx",
        ".odt",
        ".pages",
        ".pdf",
        ".rtf",
        ".tex",
        ".wpd",
        ".wps",
    }
    _EBOOK_SET: set[str] = {
        ".epub",
        # ".azw",
        # ".azw3",
        # ".cb7",
        # ".cba",
        # ".cbr",
        # ".cbt",
        # ".cbz",
        # ".djvu",
        # ".fb2",
        # ".ibook",
        # ".inf",
        # ".kfx",
        # ".lit",
        # ".mobi",
        # ".pdb"
        # ".prc",
    }
    _FONT_SET: set[str] = {
        ".fon",
        ".otf",
        ".ttc",
        ".ttf",
        ".woff",
        ".woff2",
    }
    _IMAGE_ANIMATED_SET: set[str] = {
        ".apng",
        ".gif",
        ".webp",
    }
    _IMAGE_RAW_SET: set[str] = {
        ".arw",
        ".cr2",
        ".cr3",
        ".crw",
        ".dng",
        ".nef",
        ".orf",
        ".raf",
        ".raw",
        ".rw2",
    }
    _IMAGE_VECTOR_SET: set[str] = {".svg"}
    _IMAGE_RASTER_SET: set[str] = {
        ".apng",
        ".avif",
        ".bmp",
        ".exr",
        ".gif",
        ".heic",
        ".heif",
        ".j2k",
        ".jfif",
        ".jp2",
        ".jpeg_large",
        ".jpeg",
        ".jpg_large",
        ".jpg",
        ".jpg2",
        ".jxl",
        ".png",
        ".psb",
        ".psd",
        ".tif",
        ".tiff",
        ".webp",
    }
    _INSTALLER_SET: set[str] = {".appx", ".msi", ".msix"}
    _MATERIAL_SET: set[str] = {".mtl"}
    _MODEL_SET: set[str] = {".3ds", ".fbx", ".obj", ".stl"}
    _OPEN_DOCUMENT_SET: set[str] = {
        ".fodg",
        ".fodp",
        ".fods",
        ".fodt",
        ".mscz",
        ".odf",
        ".odg",
        ".odp",
        ".ods",
        ".odt",
    }
    _PACKAGE_SET: set[str] = {
        ".aab",
        ".akp",
        ".apk",
        ".apkm",
        ".apks",
        ".pkg",
        ".xapk",
    }
    _PDF_SET: set[str] = {
        ".pdf",
    }
    _PLAINTEXT_SET: set[str] = {
        ".bat",
        ".cfg",
        ".conf",
        ".cpp",
        ".cs",
        ".css",
        ".csv",
        ".fgd",
        ".gi",
        ".h",
        ".hpp",
        ".htm",
        ".html",
        ".inf",
        ".ini",
        ".js",
        ".json",
        ".jsonc",
        ".kv3",
        ".lua",
        ".md",
        ".nut",
        ".php",
        ".plist",
        ".prefs",
        ".py",
        ".pyc",
        ".qss",
        ".sh",
        ".toml",
        ".ts",
        ".txt",
        ".vcfg",
        ".vdf",
        ".vmt",
        ".vqlayout",
        ".vsc",
        ".vsnd_template",
        ".xml",
        ".yaml",
        ".yml",
    }
    _PRESENTATION_SET: set[str] = {
        ".key",
        ".odp",
        ".ppt",
        ".pptx",
    }
    _PROGRAM_SET: set[str] = {".app", ".exe"}
    _SOURCE_ENGINE_SET: set[str] = {
        ".vtf",
    }
    _SHORTCUT_SET: set[str] = {".desktop", ".lnk", ".url"}
    _SPREADSHEET_SET: set[str] = {
        ".csv",
        ".numbers",
        ".ods",
        ".xls",
        ".xlsx",
    }
    _VIDEO_SET: set[str] = {
        ".3gp",
        ".avi",
        ".flv",
        ".gifv",
        ".hevc",
        ".m4p",
        ".m4v",
        ".mkv",
        ".mov",
        ".mp4",
        ".webm",
        ".wmv",
    }

    ADOBE_PHOTOSHOP_TYPES: MediaCategory = MediaCategory(
        media_type=MediaType.ADOBE_PHOTOSHOP,
        extensions=_ADOBE_PHOTOSHOP_SET,
        is_iana=False,
        name="photoshop",
    )
    AFFINITY_PHOTO_TYPES: MediaCategory = MediaCategory(
        media_type=MediaType.AFFINITY_PHOTO,
        extensions=_AFFINITY_PHOTO_SET,
        is_iana=False,
        name="affinity photo",
    )
    ARCHIVE_TYPES: MediaCategory = MediaCategory(
        media_type=MediaType.ARCHIVE,
        extensions=_ARCHIVE_SET,
        is_iana=False,
        name="archive",
    )
    AUDIO_MIDI_TYPES: MediaCategory = MediaCategory(
        media_type=MediaType.AUDIO_MIDI,
        extensions=_AUDIO_MIDI_SET,
        is_iana=False,
        name="audio midi",
    )
    AUDIO_TYPES: MediaCategory = MediaCategory(
        media_type=MediaType.AUDIO,
        extensions=_AUDIO_SET | _AUDIO_MIDI_SET,
        is_iana=True,
        name="audio",
    )
    BLENDER_TYPES: MediaCategory = MediaCategory(
        media_type=MediaType.BLENDER,
        extensions=_BLENDER_SET,
        is_iana=False,
        name="blender",
    )
    DATABASE_TYPES: MediaCategory = MediaCategory(
        media_type=MediaType.DATABASE,
        extensions=_DATABASE_SET,
        is_iana=False,
        name="database",
    )
    DISK_IMAGE_TYPES: MediaCategory = MediaCategory(
        media_type=MediaType.DISK_IMAGE,
        extensions=_DISK_IMAGE_SET,
        is_iana=False,
        name="disk image",
    )
    DOCUMENT_TYPES: MediaCategory = MediaCategory(
        media_type=MediaType.DOCUMENT,
        extensions=_DOCUMENT_SET,
        is_iana=False,
        name="document",
    )
    EBOOK_TYPES: MediaCategory = MediaCategory(
        media_type=MediaType.EBOOK,
        extensions=_EBOOK_SET,
        is_iana=False,
        name="ebook",
    )
    FONT_TYPES: MediaCategory = MediaCategory(
        media_type=MediaType.FONT,
        extensions=_FONT_SET,
        is_iana=True,
        name="font",
    )
    IMAGE_ANIMATED_TYPES: MediaCategory = MediaCategory(
        media_type=MediaType.IMAGE_ANIMATED,
        extensions=_IMAGE_ANIMATED_SET,
        is_iana=False,
        name="animated image",
    )
    IMAGE_RAW_TYPES: MediaCategory = MediaCategory(
        media_type=MediaType.IMAGE_RAW,
        extensions=_IMAGE_RAW_SET,
        is_iana=False,
        name="raw image",
    )
    IMAGE_VECTOR_TYPES: MediaCategory = MediaCategory(
        media_type=MediaType.IMAGE_VECTOR,
        extensions=_IMAGE_VECTOR_SET,
        is_iana=False,
        name="vector image",
    )
    IMAGE_RASTER_TYPES: MediaCategory = MediaCategory(
        media_type=MediaType.IMAGE,
        extensions=_IMAGE_RASTER_SET,
        is_iana=False,
        name="raster image",
    )
    IMAGE_TYPES: MediaCategory = MediaCategory(
        media_type=MediaType.IMAGE,
        extensions=_IMAGE_RASTER_SET | _IMAGE_RAW_SET | _IMAGE_VECTOR_SET,
        is_iana=True,
        name="image",
    )
    INSTALLER_TYPES: MediaCategory = MediaCategory(
        media_type=MediaType.INSTALLER,
        extensions=_INSTALLER_SET,
        is_iana=False,
        name="installer",
    )
    MATERIAL_TYPES: MediaCategory = MediaCategory(
        media_type=MediaType.MATERIAL,
        extensions=_MATERIAL_SET,
        is_iana=False,
        name="material",
    )
    MODEL_TYPES: MediaCategory = MediaCategory(
        media_type=MediaType.MODEL,
        extensions=_MODEL_SET,
        is_iana=True,
        name="model",
    )
    OPEN_DOCUMENT_TYPES: MediaCategory = MediaCategory(
        media_type=MediaType.OPEN_DOCUMENT,
        extensions=_OPEN_DOCUMENT_SET,
        is_iana=False,
        name="open document",
    )
    PACKAGE_TYPES: MediaCategory = MediaCategory(
        media_type=MediaType.PACKAGE,
        extensions=_PACKAGE_SET,
        is_iana=False,
        name="package",
    )
    PDF_TYPES: MediaCategory = MediaCategory(
        media_type=MediaType.PDF,
        extensions=_PDF_SET,
        is_iana=False,
        name="pdf",
    )
    PLAINTEXT_TYPES: MediaCategory = MediaCategory(
        media_type=MediaType.PLAINTEXT,
        extensions=_PLAINTEXT_SET,
        is_iana=False,
        name="plaintext",
    )
    PRESENTATION_TYPES: MediaCategory = MediaCategory(
        media_type=MediaType.PRESENTATION,
        extensions=_PRESENTATION_SET,
        is_iana=False,
        name="presentation",
    )
    PROGRAM_TYPES: MediaCategory = MediaCategory(
        media_type=MediaType.PROGRAM,
        extensions=_PROGRAM_SET,
        is_iana=False,
        name="program",
    )
    SHORTCUT_TYPES: MediaCategory = MediaCategory(
        media_type=MediaType.SHORTCUT,
        extensions=_SHORTCUT_SET,
        is_iana=False,
        name="shortcut",
    )
    SOURCE_ENGINE_TYPES: MediaCategory = MediaCategory(
        media_type=MediaType.SOURCE_ENGINE,
        extensions=_SOURCE_ENGINE_SET,
        is_iana=False,
        name="source engine",
    )
    SPREADSHEET_TYPES: MediaCategory = MediaCategory(
        media_type=MediaType.SPREADSHEET,
        extensions=_SPREADSHEET_SET,
        is_iana=False,
        name="spreadsheet",
    )
    TEXT_TYPES: MediaCategory = MediaCategory(
        media_type=MediaType.TEXT,
        extensions=_DOCUMENT_SET | _PLAINTEXT_SET,
        is_iana=True,
        name="text",
    )
    VIDEO_TYPES: MediaCategory = MediaCategory(
        media_type=MediaType.VIDEO,
        extensions=_VIDEO_SET,
        is_iana=True,
        name="video",
    )

    ALL_CATEGORIES: list[MediaCategory] = [
        ADOBE_PHOTOSHOP_TYPES,
        AFFINITY_PHOTO_TYPES,
        ARCHIVE_TYPES,
        AUDIO_MIDI_TYPES,
        AUDIO_TYPES,
        BLENDER_TYPES,
        DATABASE_TYPES,
        DISK_IMAGE_TYPES,
        DOCUMENT_TYPES,
        EBOOK_TYPES,
        FONT_TYPES,
        IMAGE_ANIMATED_TYPES,
        IMAGE_RAW_TYPES,
        IMAGE_TYPES,
        IMAGE_VECTOR_TYPES,
        INSTALLER_TYPES,
        MATERIAL_TYPES,
        MODEL_TYPES,
        OPEN_DOCUMENT_TYPES,
        PACKAGE_TYPES,
        PDF_TYPES,
        PLAINTEXT_TYPES,
        PRESENTATION_TYPES,
        PROGRAM_TYPES,
        SHORTCUT_TYPES,
        SOURCE_ENGINE_TYPES,
        SPREADSHEET_TYPES,
        TEXT_TYPES,
        VIDEO_TYPES,
    ]

    @staticmethod
    def get_types(ext: str, mime_fallback: bool = False) -> set[MediaType]:
        """Return a set of MediaTypes given a file extension.

        Args:
            ext (str): File extension with a leading "." and in all lowercase.
            mime_fallback (bool): Flag to guess MIME type if no set matches are made.
        """
        media_types: set[MediaType] = set()
        # mime_guess: bool = False

        for cat in MediaCategories.ALL_CATEGORIES:
            if ext in cat.extensions:
                media_types.add(cat.media_type)
            elif mime_fallback and cat.is_iana:
                mime_type: str = mimetypes.guess_type(Path("x" + ext), strict=False)[0]
                if mime_type and mime_type.startswith(cat.media_type.value):
                    media_types.add(cat.media_type)
                    # mime_guess = True
        return media_types

    @staticmethod
    def is_ext_in_category(ext: str, media_cat: MediaCategory, mime_fallback: bool = False) -> bool:
        """Check if an extension is a member of a MediaCategory.

        Args:
            ext (str): File extension with a leading "." and in all lowercase.
            media_cat (MediaCategory): The MediaCategory to to check for extension membership.
            mime_fallback (bool): Flag to guess MIME type if no set matches are made.
        """
        if ext in media_cat.extensions:
            return True
        elif mime_fallback and media_cat.is_iana:
            mime_type: str = mimetypes.guess_type(Path("x" + ext), strict=False)[0]
            if mime_type and mime_type.startswith(media_cat.media_type.value):
                return True
        return False
