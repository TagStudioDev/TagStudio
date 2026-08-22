# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


import enum
import mimetypes
from dataclasses import dataclass
from enum import Enum, auto
from pathlib import Path

import structlog

from tagstudio.core.utils.sanitized_attr import SanitizedAttr

logger = structlog.get_logger(__name__)


class Context(Enum):
    """An enum representing the use for a media type."""

    SEARCH = auto()
    RENDER = auto()


class _Type:
    """A complete description of a media type and its uses."""

    def __init__(self, exts: str | list[str], contexts: Context | list[Context]) -> None:
        if isinstance(exts, str):
            self.exts = [exts]
        else:
            self.exts = exts

        if isinstance(contexts, Context):
            self.contexts = [contexts]
        else:
            self.contexts = contexts


class MediaTypeGroup:
    def __init__(self, name_key: str, types: list[_Type]) -> None:
        self.searchable: frozenset[str]  # TODO: Make these dynamic
        self.renderable: frozenset[str]  # TODO: Make these dynamic
        self.name_key = name_key
        self.types = types
        # NOTE: Does self.types need to exist?
        # TODO: Handle equivalencies

        searchable_set: set[str] = set()
        renderable_set: set[str] = set()
        for type_ in self.types:
            if Context.SEARCH in type_.contexts:
                for ext in type_.exts:
                    searchable_set.add(ext)

            if Context.RENDER in type_.contexts:
                for ext in type_.exts:
                    renderable_set.add(ext)

        self.searchable = frozenset(searchable_set)
        self.renderable = frozenset(renderable_set)

    def contains(self, ext: str, context: Context) -> bool:
        # logger.info(f"MIME Guess: {mimetypes.guess_type(Path(f'x{ext}'), strict=False)}")
        return (
            context == Context.SEARCH
            and ext in self.searchable
            or context == Context.RENDER
            and ext in self.renderable
        )
        # return True

        # if self.is_iana:
        #     mime_type: str | None = mimetypes.guess_type(Path(f"x{ext}"), strict=False)[0]
        #     if mime_type is not None and mime_type.startswith(self.name_key):
        #         logger.info(f"MIME type found for {ext}: {mime_type}")
        #         return True

        # return False


class MediaTypes(metaclass=SanitizedAttr):
    # TODO: Implement filename equivalencies
    # TODO: Implement in_all_groups or something, if needed
    # TODO: Implement collision detection (e.g. ".ts")

    @staticmethod
    def register(group: MediaTypeGroup) -> None:
        setattr(MediaTypes, group.name_key.replace(".", "_"), group)


SEARCH, RENDER = Context.SEARCH, Context.RENDER

# Adobe ----------------------------------------------------------------------------------------

# TODO: Don't have these floating in the global space
_adobe_photoshop = MediaTypeGroup(
    "adobe.photoshop",
    [
        _Type(".pdd", SEARCH),
        _Type(".psb", SEARCH),
        _Type(".psd", SEARCH),
    ],
)
MediaTypes.register(_adobe_photoshop)

_adobe_illustrator = MediaTypeGroup(
    "adobe.illustrator",
    [
        _Type(".ai", SEARCH),
    ],
)
MediaTypes.register(_adobe_illustrator)

_pdf = MediaTypeGroup(
    "pdf",
    [
        _Type(".pdf", [SEARCH, RENDER]),
        _Type(".ai", RENDER),
    ],
)
MediaTypes.register(_pdf)

adobe = MediaTypeGroup("adobe", _adobe_photoshop.types + _adobe_illustrator.types + _pdf.types)
MediaTypes.register(adobe)

# Affinity -------------------------------------------------------------------------------------
affinity_photo = MediaTypeGroup(
    "affinity.photo",
    [_Type(".afphoto", [SEARCH, RENDER])],
)
affinity_designer = MediaTypeGroup(
    "affinity.designer",
    [_Type(".afdesign", [SEARCH, RENDER])],
)
affinity_publisher = MediaTypeGroup(
    "affinity.publisher",
    [_Type([".afpublisher", ".afpub"], [SEARCH, RENDER])],
)

affinity = MediaTypeGroup(
    "affinity",
    affinity_photo.types
    + affinity_designer.types
    + affinity_publisher.types
    + [_Type(".af", [SEARCH, RENDER])],
)

# Blender --------------------------------------------------------------------------------------
_blender = MediaTypeGroup(
    "blender",
    [
        _Type(".blen_tc", [SEARCH, RENDER]),
        _Type(".blend", [SEARCH, RENDER]),
        # Numbered Blender auto-backup files (.blend1 - .blend32)
        _Type([f".blend{i}" for i in range(1, 33)], [SEARCH, RENDER]),
    ],
)
MediaTypes.register(_blender)

# Clip Studio Paint ----------------------------------------------------------------------------
clip_studio_paint = MediaTypeGroup(
    "clip_studio_paint",
    [
        _Type(".lip", [SEARCH, RENDER]),
        _Type(".clip", [SEARCH, RENDER]),
        _Type(".cmc", [SEARCH, RENDER]),
    ],
)
MediaTypes.register(clip_studio_paint)

# Krita ----------------------------------------------------------------------------------------
krita = MediaTypeGroup(
    "krita",
    [
        _Type(".kra", [SEARCH, RENDER]),
        _Type(".krz", [SEARCH, RENDER]),
    ],
)
MediaTypes.register(krita)

# MediBang Paint / FireAlpaca ------------------------------------------------------------------
medibang_paint = MediaTypeGroup("medibang_paint", [_Type(".mdp", [SEARCH, RENDER])])
MediaTypes.register(medibang_paint)

# Paint.NET ------------------------------------------------------------------------------------
paint_dot_net = MediaTypeGroup("paint_dot_net", [_Type(".pdn", [SEARCH, RENDER])])
MediaTypes.register(paint_dot_net)

# Archives -------------------------------------------------------------------------------------
archive = MediaTypeGroup(
    "archive",
    [
        _Type(".7z", [SEARCH, RENDER]),
        _Type(".gz", SEARCH),
        _Type(".rar", [SEARCH, RENDER]),
        _Type(".s7z", [SEARCH, RENDER]),
        _Type(".tar", [SEARCH, RENDER]),
        _Type(".tgz", [SEARCH, RENDER]),
        _Type(".zip", [SEARCH, RENDER]),
    ],
)
MediaTypes.register(archive)

# eBooks -------------------------------------------------------------------------------------
ebook = MediaTypeGroup(
    "ebook",
    [
        _Type(".azw", [SEARCH, RENDER]),
        _Type(".azw3", [SEARCH, RENDER]),
        _Type(".cb7", [SEARCH, RENDER]),
        _Type(".cba", [SEARCH, RENDER]),
        _Type(".cbr", [SEARCH, RENDER]),
        _Type(".cbt", [SEARCH, RENDER]),
        _Type(".cbz", [SEARCH, RENDER]),
        _Type(".djvu", [SEARCH, RENDER]),
        _Type(".epub", [SEARCH, RENDER]),
        _Type(".fb2", [SEARCH, RENDER]),
        _Type(".ibook", [SEARCH, RENDER]),
        _Type(".inf", [SEARCH, RENDER]),
        _Type(".kfx", [SEARCH, RENDER]),
        _Type(".lit", [SEARCH, RENDER]),
        _Type(".mobi", [SEARCH, RENDER]),
        _Type(".pdb", [SEARCH, RENDER]),
        _Type(".prc", [SEARCH, RENDER]),
        _Type(".mscz", RENDER),
    ],
)
MediaTypes.register(ebook)

# Fonts --------------------------------------------------------------------------------------
font = MediaTypeGroup(
    "font",
    [
        _Type(".fon", SEARCH),
        _Type(".otf", [SEARCH, RENDER]),
        _Type(".ttc", [SEARCH, RENDER]),
        _Type(".ttf", [SEARCH, RENDER]),
        _Type(".woff", [SEARCH, RENDER]),
        _Type(".woff2", [SEARCH, RENDER]),
    ],
)
MediaTypes.register(font)

# Office & Documents ---------------------------------------------------------------------------
document = MediaTypeGroup(
    "document",
    [
        _Type(".doc", SEARCH),
        _Type(".docm", SEARCH),
        _Type(".docx", SEARCH),
        _Type(".dot", SEARCH),
        _Type(".dotm", SEARCH),
        _Type(".dotx", SEARCH),
        _Type(".odt", SEARCH),
        _Type(".pages", SEARCH),
        _Type(".pdf", SEARCH),
        _Type(".pxd", SEARCH),
        _Type(".rtf", SEARCH),
        _Type(".tex", SEARCH),
        _Type(".wpd", SEARCH),
        _Type(".wps", SEARCH),
    ],
)
open_document = MediaTypeGroup(
    "open_document",
    [
        _Type(".fodg", [SEARCH, RENDER]),
        _Type(".fodp", [SEARCH, RENDER]),
        _Type(".fods", [SEARCH, RENDER]),
        _Type(".fodt", [SEARCH, RENDER]),
        _Type(".mscz", SEARCH),
        _Type(".odf", [SEARCH, RENDER]),
        _Type(".odg", [SEARCH, RENDER]),
        _Type(".odp", [SEARCH, RENDER]),
        _Type(".ods", [SEARCH, RENDER]),
        _Type(".odt", [SEARCH, RENDER]),
        _Type(".ora", [SEARCH, RENDER]),
    ],
)
MediaTypes.register(open_document)

iwork = MediaTypeGroup(
    "iwork",
    [
        _Type(".key", [SEARCH, RENDER]),
        _Type(".numbers", [SEARCH, RENDER]),
        _Type(".pages", [SEARCH, RENDER]),
        _Type(".pxd", RENDER),
    ],
)
MediaTypes.register(iwork)

powerpoint = MediaTypeGroup(
    "office.powerpoint",
    [
        _Type(".ppt", SEARCH),
        _Type(".pptx", [SEARCH, RENDER]),
    ],
)
MediaTypes.register(powerpoint)

presentation = MediaTypeGroup(
    "presentation",
    [
        _Type(".key", SEARCH),
        _Type(".odp", SEARCH),
    ]
    + powerpoint.types,
)
MediaTypes.register(presentation)

spreadsheet = MediaTypeGroup(
    "spreadsheet",
    [
        _Type(".csv", SEARCH),
        _Type(".numbers", SEARCH),
        _Type(".ods", SEARCH),
        _Type(".xls", SEARCH),
        _Type(".xlsx", SEARCH),
    ],
)
MediaTypes.register(spreadsheet)

# 3D -------------------------------------------------------------------------------------------
model = MediaTypeGroup(
    "model",
    [
        _Type(".3ds", SEARCH),
        _Type(".fbx", SEARCH),
        _Type(".obj", SEARCH),
        _Type(".stl", SEARCH),
    ],
)
MediaTypes.register(model)

material = MediaTypeGroup(
    "material",
    [
        _Type(".mtl", SEARCH),
    ],
)
MediaTypes.register(material)

shader = MediaTypeGroup(
    "shader",
    [
        _Type(".effect", SEARCH),
        _Type(".frag", SEARCH),
        _Type(".fsh", SEARCH),
        _Type(".glsl", SEARCH),
        _Type(".shader", SEARCH),
        _Type(".vert", SEARCH),
        _Type(".vsh", SEARCH),
    ],
)
MediaTypes.register(shader)

# System & Misc ------------------------------------------------------------------------------
database = MediaTypeGroup(
    "database",
    [
        _Type(".accdb", SEARCH),
        _Type(".mdb", SEARCH),
        _Type(".pdb", SEARCH),
        _Type(".db", SEARCH),
        _Type(".sqlite", SEARCH),
        _Type(".sqlite3", SEARCH),
    ],
)
MediaTypes.register(database)

disk_image = MediaTypeGroup(
    "disk_image",
    [
        _Type(".bios", SEARCH),
        _Type(".dmg", SEARCH),
        _Type(".fhdx", SEARCH),
        _Type(".iso", SEARCH),
    ],
)
MediaTypes.register(disk_image)

installer = MediaTypeGroup(
    "installer",
    [
        _Type(".appx", SEARCH),
        _Type(".msi", SEARCH),
        _Type(".msix", SEARCH),
    ],
)
MediaTypes.register(installer)

package = MediaTypeGroup(
    "package",
    [
        _Type(".aab", SEARCH),
        _Type(".akp", SEARCH),
        _Type(".apk", SEARCH),
        _Type(".apkm", SEARCH),
        _Type(".apks", SEARCH),
        _Type(".pkg", SEARCH),
        _Type(".xapk", SEARCH),
    ],
)
MediaTypes.register(package)

program = MediaTypeGroup(
    "program",
    [
        _Type(".app", SEARCH),
        _Type(".bin", SEARCH),
        _Type(".exe", SEARCH),
    ],
)
MediaTypes.register(program)

shortcut = MediaTypeGroup(
    "shortcut",
    [
        _Type(".desktop", SEARCH),
        _Type(".lnk", SEARCH),
        _Type(".url", SEARCH),
    ],
)
MediaTypes.register(shortcut)

# Valve Source Engine --------------------------------------------------------------------------
source_engine = MediaTypeGroup(
    "source_engine",
    [_Type(".vtf", [SEARCH, RENDER])],
)
MediaTypes.register(source_engine)

# MIDI -----------------------------------------------------------------------------------------
midi = MediaTypeGroup("midi", [_Type([".mid", ".midi"], SEARCH)])
MediaTypes.register(midi)

# Audio ----------------------------------------------------------------------------------------
audio = MediaTypeGroup(
    "audio",
    [
        _Type(".aac", [RENDER, SEARCH]),
        _Type(
            [".aif", ".aiff", ".aifc"],
            [RENDER, SEARCH],
        ),
        _Type(".caf", [RENDER, SEARCH]),
        _Type(".flac", [RENDER, SEARCH]),
        _Type(".m4a", [RENDER, SEARCH]),
        _Type(".m4p", [RENDER, SEARCH]),
        _Type(".mp3", [RENDER, SEARCH]),
        _Type(".ogg", [RENDER, SEARCH]),
        _Type(".wav", [RENDER, SEARCH]),
        _Type(".wma", [RENDER, SEARCH]),
    ]
    + midi.types,
)
MediaTypes.register(audio)

# RAW Images -----------------------------------------------------------------------------------
raw_image = MediaTypeGroup(
    "image.raw",
    [
        _Type(".arw", [SEARCH, RENDER]),
        _Type(".cr2", [SEARCH, RENDER]),
        _Type(".cr3", [SEARCH, RENDER]),
        _Type(".crw", [SEARCH, RENDER]),
        _Type(".dng", [SEARCH, RENDER]),
        _Type(".nef", [SEARCH, RENDER]),
        _Type(".nrw", [SEARCH, RENDER]),
        _Type(".orf", [SEARCH, RENDER]),
        _Type(".r3d", [SEARCH, RENDER]),
        _Type(".raf", [SEARCH, RENDER]),
        _Type(".raw", [SEARCH, RENDER]),
        _Type(".rw2", [SEARCH, RENDER]),
        _Type(".srf", [SEARCH, RENDER]),
        _Type(".srf2", [SEARCH, RENDER]),
    ],
)
MediaTypes.register(raw_image)

# Raster Images --------------------------------------------------------------------------------
raster_image = MediaTypeGroup(
    "image.raster",
    [
        _Type(".apng", [SEARCH, RENDER]),
        _Type(".avif", [SEARCH, RENDER]),
        _Type(".bmp", [SEARCH, RENDER]),
        _Type(".exr", [SEARCH, RENDER]),
        _Type(".gif", [SEARCH, RENDER]),
        _Type(
            [
                ".jfif",
                ".jpeg_large",
                ".jpeg",
                ".jpg_large",
                ".jpg",
            ],
            [SEARCH, RENDER],
        ),
        _Type(".jxl", [SEARCH, RENDER]),
        _Type(".png", [SEARCH, RENDER]),
        _Type(".psb", RENDER),
        _Type(".psd", RENDER),
        _Type(".webp", [SEARCH, RENDER]),
        _Type([".heic", ".heif"], [SEARCH, RENDER]),
        _Type([".j2k", ".jp2", ".jpg2"], [SEARCH, RENDER]),
        _Type([".tif", ".tiff"], [SEARCH, RENDER]),
    ],
)
MediaTypes.register(raster_image)

# Vector Images --------------------------------------------------------------------------------
vector_image = MediaTypeGroup(
    "image.vector",
    [
        _Type(".eps", SEARCH),
        _Type(".epsf", SEARCH),
        _Type(".epsi", SEARCH),
        _Type(".svg", [SEARCH, RENDER]),
        _Type(".svgz", SEARCH),
    ],
)
MediaTypes.register(vector_image)

# Animated Images ------------------------------------------------------------------------------
animated_image = MediaTypeGroup(
    "image.animated",
    [
        _Type(".gif", [SEARCH, RENDER]),
        _Type(".apng", [SEARCH, RENDER]),
        _Type(".webp", [SEARCH, RENDER]),
        _Type(".jxl", SEARCH),
    ],
)

# Binary ---------------------------------------------------------------------------------------
binary = MediaTypeGroup(
    "binary",
    [
        _Type(".dll", [RENDER, SEARCH]),
        _Type(".dylib", [RENDER, SEARCH]),
        _Type(".exe", [RENDER, SEARCH]),
        _Type(".o", [RENDER, SEARCH]),
        _Type(".pyc", [RENDER, SEARCH]),
        _Type(".pyd", [RENDER, SEARCH]),
        _Type(".pyo", [RENDER, SEARCH]),
    ],
)

# Python ---------------------------------------------------------------------------------------
python = MediaTypeGroup(
    "python",
    [
        _Type(".ipynb", [RENDER, SEARCH]),
        _Type(".py", [RENDER, SEARCH]),
        _Type(".pyc", SEARCH),
        _Type(".pyd", SEARCH),
        _Type(".pyi", [RENDER, SEARCH]),
        _Type(".pyo", SEARCH),
    ],
)

# JavaScript -----------------------------------------------------------------------------------
javascript = MediaTypeGroup(
    "javascript",
    [
        _Type(".cjs", [SEARCH, RENDER]),
        _Type(".js", [SEARCH, RENDER]),
        _Type(".jsx", [SEARCH, RENDER]),
        _Type(".mjs", [SEARCH, RENDER]),
    ],
)

# TypeScript -----------------------------------------------------------------------------------
typescript = MediaTypeGroup(
    "typescript",
    [
        _Type(".cts", [SEARCH, RENDER]),
        _Type(".mts", [SEARCH, RENDER]),
        # _Type(".ts", [SEARCH, RENDER]),
        _Type(".tsx", [SEARCH, RENDER]),
    ],
)

# Shell Script ---------------------------------------------------------------------------------
shell = MediaTypeGroup(
    "shell",
    [
        _Type(".bat", [SEARCH, RENDER]),
        _Type(".csh", [SEARCH, RENDER]),
        _Type(".fish", [SEARCH, RENDER]),
        _Type(".nu", [SEARCH, RENDER]),
        _Type(".ps1", [SEARCH, RENDER]),
        _Type(".sh", [SEARCH, RENDER]),
        _Type("activate", [SEARCH, RENDER]),
    ],
)

# Markdown -------------------------------------------------------------------------------------
markdown = MediaTypeGroup(
    "markdown",
    [
        _Type(
            [
                ".markdown",
                ".md",
                ".mkd",
                ".rmd",
            ],
            [SEARCH, RENDER],
        ),
    ],
)

# Markup ---------------------------------------------------------------------------------------
markup = MediaTypeGroup(
    "markup",
    [
        _Type(
            [
                ".yml",
                ".yaml",
            ],
            [SEARCH, RENDER],
        ),
        _Type(
            [
                ".json",
                ".jsonc",
                ".json5",
                ".jsonl",
            ],
            [SEARCH, RENDER],
        ),
        _Type(
            [
                ".xml",
                ".xul",
            ],
            [SEARCH, RENDER],
        ),
        _Type(
            [
                ".html",
                ".htm",
                ".xhtml",
                ".shtml",
                ".dhtml",
            ],
            [SEARCH, RENDER],
        ),
        _Type(
            [
                ".plist",
            ],
            [SEARCH, RENDER],
        ),
        _Type(".toml", [SEARCH, RENDER]),
    ],
)

# Code -----------------------------------------------------------------------------------------
code = MediaTypeGroup(
    "code",
    [
        _Type(".lock", [SEARCH, RENDER]),
        _Type(".log", [SEARCH, RENDER]),
    ]
    + python.types
    + javascript.types
    + typescript.types
    + shell.types
    + markdown.types
    + markup.types,
)
MediaTypes.register(code)

# Plaintext ------------------------------------------------------------------------------------
plaintext = MediaTypeGroup(
    "plaintext",
    [
        _Type(".i3u", [SEARCH, RENDER]),
        _Type(".lang", [SEARCH, RENDER]),
        _Type("contributing", [SEARCH, RENDER]),
        _Type("license", [SEARCH, RENDER]),
        _Type("readme", [SEARCH, RENDER]),
        _Type([".txt", ".text"], [SEARCH, RENDER]),
    ],
)
MediaTypes.register(plaintext)

# Video ----------------------------------------------------------------------------------------
video = MediaTypeGroup(
    "video",
    [
        _Type(".3gp", [SEARCH, RENDER]),
        _Type(".avi", [SEARCH, RENDER]),
        _Type(".flv", [SEARCH, RENDER]),
        _Type(".gifv", [SEARCH, RENDER]),
        _Type(".hevc", [SEARCH, RENDER]),
        _Type(".m4p", [SEARCH, RENDER]),
        _Type(".m4v", [SEARCH, RENDER]),
        _Type(".mkv", [SEARCH, RENDER]),
        _Type(".mov", [SEARCH, RENDER]),
        _Type(".mp4", [SEARCH, RENDER]),
        _Type(".webm", [SEARCH, RENDER]),
        _Type(".wmv", [SEARCH, RENDER]),
    ],
)
MediaTypes.register(video)

# ------------------

# @staticmethod
# def all_media_types():
#     static_methods = [
#         name for name, attr in MediaTypes.__dict__.items() if isinstance(attr, MediaTypeGroup)
#     ]
#     return static_methods


FILETYPE_EQUIVALENTS = [
    {"aif", "aiff", "aifc"},
    {"html", "htm", "xhtml", "shtml", "dhtml"},
    {"jfif", "jpeg_large", "jpeg", "jpg_large", "jpg"},
    {"json", "jsonc", "json5", "jsonl"},
    {"md", "markdown", "mkd", "rmd"},
    {"tar.gz", "tgz"},
    {"xml", "xul"},
    {"yaml", "yml"},
]


class MediaTypeOld(enum.StrEnum):
    """Names of media types."""

    ADOBE_PHOTOSHOP = "adobe_photoshop"
    AFFINITY_PHOTO = "affinity_photo"
    ARCHIVE = "archive"
    AUDIO_MIDI = "audio_midi"
    AUDIO = "audio"
    BLENDER = "blender"
    CLIP_STUDIO_PAINT = "clip_studio_paint"
    CODE = "code"
    DATABASE = "database"
    DISK_IMAGE = "disk_image"
    DOCUMENT = "document"
    EBOOK = "ebook"
    FONT = "font"
    IMAGE_ANIMATED = "image_animated"
    IMAGE_RAW = "image_raw"
    IMAGE_VECTOR = "image_vector"
    IMAGE = "image"
    INSTALLER = "installer"
    IWORK = "iwork"
    MATERIAL = "material"
    MDIPACK = "mdipack"
    MODEL = "model"
    OPEN_DOCUMENT = "open_document"
    PACKAGE = "package"
    PAINT_DOT_NET = "paint_dot_net"
    PDF = "pdf"
    PLAINTEXT = "plaintext"
    PRESENTATION = "presentation"
    PROGRAM = "program"
    SHADER = "shader"
    SHORTCUT = "shortcut"
    SOURCE_ENGINE = "source_engine"
    SPREADSHEET = "spreadsheet"
    TEXT = "text"
    VIDEO = "video"


@dataclass(frozen=True)
class MediaCategory:
    """An object representing a category of media.

    Includes a MediaType identifier, extensions set, and IANA status flag.

    Args:
        media_type (MediaType): The MediaType Enum representing this category.

        extensions (set[str]): The set of file extensions associated with this category.
            Includes leading ".", all lowercase, and does not need to be unique to this category.

        is_iana (bool): Represents whether this is an IANA registered category.
    """

    media_type: MediaTypeOld
    extensions: set[str]
    name: str
    is_iana: bool = False

    def contains(self, ext: str, mime_fallback: bool = False) -> bool:
        """Check if an extension is a member of this MediaCategory.

        Args:
            ext (str): File extension with a leading "." and in all lowercase.
            mime_fallback (bool): Flag to guess MIME type if no set matches are made.
        """
        if ext in self.extensions:
            return True
        elif mime_fallback and self.is_iana:
            mime_type: str | None = mimetypes.guess_type(Path("x" + ext), strict=False)[0]
            if mime_type is not None and mime_type.startswith(self.media_type.value):
                return True
        return False


class MediaCategories:
    """Contain pre-made MediaCategory objects as well as methods to interact with them."""

    # These sets are used either individually or together to form the final sets
    # for the MediaCategory(s).
    # These sets may be combined and are NOT 1:1 with the final categories.
    _ADOBE_ILLUSTRATOR_SET: set[str] = {".ai"}
    _ADOBE_PHOTOSHOP_SET: set[str] = {
        ".pdd",
        ".psb",
        ".psd",
    }
    _AFFINITY_PHOTO_SET: set[str] = {".afphoto"}
    _KRITA_SET: set[str] = {".kra", ".krz"}
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
        ".aifc",
        ".aiff",
        ".alac",
        ".caf",
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
    _CLIP_STUDIO_PAINT_SET: set[str] = {".clip"}
    _CODE_SET: set[str] = {
        ".bat",
        ".cfg",
        ".conf",
        ".cpp",
        ".cs",
        ".csh",
        ".css",
        ".d",
        ".dhtml",
        ".fgd",
        ".fish",
        ".gitignore",
        ".h",
        ".hpp",
        ".htm",
        ".html",
        ".inf",
        ".ini",
        ".js",
        ".json",
        ".json5",
        ".jsonc",
        ".jsx",
        ".kv3",
        ".lua",
        ".meta",
        ".nix",
        ".nu",
        ".nut",
        ".php",
        ".plist",
        ".prefs",
        ".ps1",
        ".py",
        ".pyi",
        ".qml",
        ".qrc",
        ".qss",
        ".rs",
        ".sh",
        ".shtml",
        ".sip",
        ".spec",
        ".tcl",
        ".timestamp",
        ".toml",
        ".ts",
        ".tsx",
        ".vcfg",
        ".vdf",
        ".vmt",
        ".vqlayout",
        ".vsc",
        ".vsnd_template",
        ".xhtml",
        ".xml",
        ".xul",
        ".yaml",
        ".yml",
    }
    _DATABASE_SET: set[str] = {
        ".accdb",
        ".mdb",
        ".pdb",
        ".sqlite",
        ".sqlite3",
    }
    _DISK_IMAGE_SET: set[str] = {".bios", ".dmg", ".fhdx", ".iso"}
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
        ".pxd",
        ".rtf",
        ".tex",
        ".wpd",
        ".wps",
    }
    _EBOOK_SET: set[str] = {
        ".azw",
        ".azw3",
        ".cb7",
        ".cba",
        ".cbr",
        ".cbt",
        ".cbz",
        ".djvu",
        ".epub",
        ".fb2",
        ".ibook",
        ".kfx",
        ".lit",
        ".mobi",
        ".pdb",
        ".prc",
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
        ".nrw",
        ".orf",
        ".r3d",
        ".raf",
        ".raw",
        ".rw2",
        ".srf",
        ".srf2",
    }
    _IMAGE_VECTOR_SET: set[str] = {".eps", ".epsf", ".epsi", ".svg", ".svgz"}
    _IMAGE_RASTER_SET: set[str] = {
        ".apng",
        ".avif",
        ".bmp",
        ".exr",
        ".gif",
        ".heic",
        ".heif",
        ".icns",
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
    _IWORK_SET: set[str] = {".key", ".numbers", ".pages"}
    _MATERIAL_SET: set[str] = {".mtl"}
    _MDIPACK_SET: set[str] = {".mdp"}
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
        ".ora",
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
    _PAINT_DOT_NET_SET: set[str] = {".pdn"}
    _PDF_SET: set[str] = {".pdf"}
    _PLAINTEXT_SET: set[str] = {
        ".csv",
        ".i3u",
        ".lang",
        ".lock",
        ".log",
        ".markdown",
        ".md",
        ".mkd",
        ".rmd",
        ".text",
        ".txt",
        "contributing",
        "license",
        "readme",
    }
    _PRESENTATION_SET: set[str] = {
        ".key",
        ".odp",
        ".ppt",
        ".pptx",
    }
    _PROGRAM_SET: set[str] = {".app", ".bin", ".exe"}
    _SOURCE_ENGINE_SET: set[str] = {".vtf"}
    _SHADER_SET: set[str] = {
        ".effect",
        ".frag",
        ".fsh",
        ".glsl",
        ".shader",
        ".vert",
        ".vsh",
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
        ".ts",
    }

    ADOBE_PHOTOSHOP_TYPES = MediaCategory(
        media_type=MediaTypeOld.ADOBE_PHOTOSHOP,
        extensions=_ADOBE_PHOTOSHOP_SET,
        is_iana=False,
        name="photoshop",
    )
    AFFINITY_PHOTO_TYPES = MediaCategory(
        media_type=MediaTypeOld.AFFINITY_PHOTO,
        extensions=_AFFINITY_PHOTO_SET,
        is_iana=False,
        name="affinity photo",
    )
    ARCHIVE_TYPES = MediaCategory(
        media_type=MediaTypeOld.ARCHIVE,
        extensions=_ARCHIVE_SET,
        is_iana=False,
        name="archive",
    )
    AUDIO_MIDI_TYPES = MediaCategory(
        media_type=MediaTypeOld.AUDIO_MIDI,
        extensions=_AUDIO_MIDI_SET,
        is_iana=False,
        name="audio midi",
    )
    AUDIO_TYPES = MediaCategory(
        media_type=MediaTypeOld.AUDIO,
        extensions=_AUDIO_SET | _AUDIO_MIDI_SET,
        is_iana=True,
        name="audio",
    )
    BLENDER_TYPES = MediaCategory(
        media_type=MediaTypeOld.BLENDER,
        extensions=_BLENDER_SET,
        is_iana=False,
        name="blender",
    )
    CLIP_STUDIO_PAINT_TYPES = MediaCategory(
        media_type=MediaTypeOld.CLIP_STUDIO_PAINT,
        extensions=_CLIP_STUDIO_PAINT_SET,
        is_iana=False,
        name="clip studio paint",
    )
    CODE_TYPES = MediaCategory(
        media_type=MediaTypeOld.CODE,
        extensions=_CODE_SET,
        is_iana=False,
        name="code",
    )
    DATABASE_TYPES = MediaCategory(
        media_type=MediaTypeOld.DATABASE,
        extensions=_DATABASE_SET,
        is_iana=False,
        name="database",
    )
    DISK_IMAGE_TYPES = MediaCategory(
        media_type=MediaTypeOld.DISK_IMAGE,
        extensions=_DISK_IMAGE_SET,
        is_iana=False,
        name="disk image",
    )
    DOCUMENT_TYPES = MediaCategory(
        media_type=MediaTypeOld.DOCUMENT,
        extensions=_DOCUMENT_SET,
        is_iana=False,
        name="document",
    )
    EBOOK_TYPES = MediaCategory(
        media_type=MediaTypeOld.EBOOK,
        extensions=_EBOOK_SET,
        is_iana=False,
        name="ebook",
    )
    FONT_TYPES = MediaCategory(
        media_type=MediaTypeOld.FONT,
        extensions=_FONT_SET,
        is_iana=True,
        name="font",
    )
    IMAGE_ANIMATED_TYPES = MediaCategory(
        media_type=MediaTypeOld.IMAGE_ANIMATED,
        extensions=_IMAGE_ANIMATED_SET,
        is_iana=False,
        name="animated image",
    )
    IMAGE_RAW_TYPES = MediaCategory(
        media_type=MediaTypeOld.IMAGE_RAW,
        extensions=_IMAGE_RAW_SET,
        is_iana=False,
        name="raw image",
    )
    IMAGE_VECTOR_TYPES = MediaCategory(
        media_type=MediaTypeOld.IMAGE_VECTOR,
        extensions=_IMAGE_VECTOR_SET,
        is_iana=False,
        name="vector image",
    )
    IMAGE_RASTER_TYPES = MediaCategory(
        media_type=MediaTypeOld.IMAGE,
        extensions=_IMAGE_RASTER_SET,
        is_iana=False,
        name="raster image",
    )
    IMAGE_TYPES = MediaCategory(
        media_type=MediaTypeOld.IMAGE,
        extensions=_IMAGE_RASTER_SET | _IMAGE_RAW_SET | _IMAGE_VECTOR_SET,
        is_iana=True,
        name="image",
    )
    INSTALLER_TYPES = MediaCategory(
        media_type=MediaTypeOld.INSTALLER,
        extensions=_INSTALLER_SET,
        is_iana=False,
        name="installer",
    )
    IWORK_TYPES = MediaCategory(
        media_type=MediaTypeOld.IWORK,
        extensions=_IWORK_SET,
        is_iana=False,
        name="iwork",
    )
    MATERIAL_TYPES = MediaCategory(
        media_type=MediaTypeOld.MATERIAL,
        extensions=_MATERIAL_SET,
        is_iana=False,
        name="material",
    )
    MDIPACK_TYPES = MediaCategory(
        media_type=MediaTypeOld.MDIPACK,
        extensions=_MDIPACK_SET,
        is_iana=False,
        name="mdipack",
    )
    MODEL_TYPES = MediaCategory(
        media_type=MediaTypeOld.MODEL,
        extensions=_MODEL_SET,
        is_iana=True,
        name="model",
    )
    OPEN_DOCUMENT_TYPES = MediaCategory(
        media_type=MediaTypeOld.OPEN_DOCUMENT,
        extensions=_OPEN_DOCUMENT_SET,
        is_iana=False,
        name="open document",
    )
    PACKAGE_TYPES = MediaCategory(
        media_type=MediaTypeOld.PACKAGE,
        extensions=_PACKAGE_SET,
        is_iana=False,
        name="package",
    )
    PAINT_DOT_NET_TYPES = MediaCategory(
        media_type=MediaTypeOld.PAINT_DOT_NET,
        extensions=_PAINT_DOT_NET_SET,
        is_iana=False,
        name="paint.net",
    )
    PDF_TYPES = MediaCategory(
        media_type=MediaTypeOld.PDF,
        extensions=_PDF_SET | _ADOBE_ILLUSTRATOR_SET,
        is_iana=False,
        name="pdf",
    )
    PLAINTEXT_TYPES = MediaCategory(
        media_type=MediaTypeOld.PLAINTEXT,
        extensions=_PLAINTEXT_SET | _CODE_SET,
        is_iana=False,
        name="plaintext",
    )
    PRESENTATION_TYPES = MediaCategory(
        media_type=MediaTypeOld.PRESENTATION,
        extensions=_PRESENTATION_SET,
        is_iana=False,
        name="presentation",
    )
    PROGRAM_TYPES = MediaCategory(
        media_type=MediaTypeOld.PROGRAM,
        extensions=_PROGRAM_SET,
        is_iana=False,
        name="program",
    )
    SHADER_TYPES = MediaCategory(
        media_type=MediaTypeOld.SHADER,
        extensions=_SHADER_SET,
        is_iana=False,
        name="shader",
    )
    SHORTCUT_TYPES = MediaCategory(
        media_type=MediaTypeOld.SHORTCUT,
        extensions=_SHORTCUT_SET,
        is_iana=False,
        name="shortcut",
    )
    SOURCE_ENGINE_TYPES = MediaCategory(
        media_type=MediaTypeOld.SOURCE_ENGINE,
        extensions=_SOURCE_ENGINE_SET,
        is_iana=False,
        name="source engine",
    )
    SPREADSHEET_TYPES = MediaCategory(
        media_type=MediaTypeOld.SPREADSHEET,
        extensions=_SPREADSHEET_SET,
        is_iana=False,
        name="spreadsheet",
    )
    TEXT_TYPES = MediaCategory(
        media_type=MediaTypeOld.TEXT,
        extensions=_DOCUMENT_SET | _PLAINTEXT_SET,
        is_iana=True,
        name="text",
    )
    VIDEO_TYPES = MediaCategory(
        media_type=MediaTypeOld.VIDEO,
        extensions=_VIDEO_SET,
        is_iana=True,
        name="video",
    )
    KRITA_TYPES = MediaCategory(
        media_type=MediaTypeOld.IMAGE,
        extensions=_KRITA_SET,
        is_iana=False,
        name="krita",
    )

    ALL_CATEGORIES = [
        ADOBE_PHOTOSHOP_TYPES,
        AFFINITY_PHOTO_TYPES,
        ARCHIVE_TYPES,
        AUDIO_MIDI_TYPES,
        AUDIO_TYPES,
        BLENDER_TYPES,
        CLIP_STUDIO_PAINT_TYPES,
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
        IWORK_TYPES,
        MATERIAL_TYPES,
        MDIPACK_TYPES,
        MODEL_TYPES,
        OPEN_DOCUMENT_TYPES,
        PACKAGE_TYPES,
        PAINT_DOT_NET_TYPES,
        PDF_TYPES,
        PLAINTEXT_TYPES,
        PRESENTATION_TYPES,
        PROGRAM_TYPES,
        CODE_TYPES,
        SHADER_TYPES,
        SHORTCUT_TYPES,
        SOURCE_ENGINE_TYPES,
        SPREADSHEET_TYPES,
        TEXT_TYPES,
        VIDEO_TYPES,
        KRITA_TYPES,
    ]

    @staticmethod
    def get_types(ext: str, mime_fallback: bool = False) -> set[MediaTypeOld]:
        """Return a set of MediaTypes given a file extension.

        Args:
            ext (str): File extension with a leading "." and in all lowercase.
            mime_fallback (bool): Flag to guess MIME type if no set matches are made.
        """
        media_types: set[MediaTypeOld] = set()

        for cat in MediaCategories.ALL_CATEGORIES:
            if cat.contains(ext, mime_fallback):
                media_types.add(cat.media_type)

        return media_types

    @staticmethod
    def is_ext_in_category(ext: str, media_cat: MediaCategory, mime_fallback: bool = False) -> bool:
        """Check if an extension is a member of a MediaCategory.

        Args:
            ext (str): File extension with a leading "." and in all lowercase.
            media_cat (MediaCategory): The MediaCategory to check for extension membership.
            mime_fallback (bool): Flag to guess MIME type if no set matches are made.
        """
        return media_cat.contains(ext, mime_fallback)
