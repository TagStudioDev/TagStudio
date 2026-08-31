# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


import enum
import mimetypes
from dataclasses import dataclass
from pathlib import Path
from warnings import deprecated

import structlog

from tagstudio.core.utils.sanitized_attr import SanitizedAttr

logger = structlog.get_logger(__name__)


SEARCH = "SEARCH"


class MediaType:
    """A complete description of a media type and its uses."""

    def __init__(self, exts: str | list[str], contexts: str | list[str]) -> None:
        self.exts: set[str]
        self.contexts: set[str]

        if isinstance(exts, str):
            self.exts = set([exts])
        else:
            self.exts = set(exts)

        if isinstance(contexts, str):
            self.contexts = set([contexts])
        else:
            self.contexts = set(contexts)


class MediaTypeGroup:
    def __init__(self, name_key: str, types: list[MediaType]) -> None:
        self.context_sets: dict[str, set[str]] = {}
        self.name_aliases: list[str] = []
        self.name_key = name_key
        self.types: list[MediaType] = []
        self.add_types(types)

    def add_types(self, types: list[MediaType]) -> None:
        for type_ in types:
            updated_types: set[MediaType] = set()
            for existing_type in self.types:
                # If there's any overlap between the extensions, it's the same type
                if not existing_type.exts.isdisjoint(type_.exts):
                    existing_type.contexts = existing_type.contexts.union(type_.contexts)
                    existing_type.exts = existing_type.exts.union(type_.exts)
                    updated_types.add(type_)
            if type_ not in updated_types:
                self.types.append(type_)

            contexts_ = [type_.contexts] if isinstance(type_.contexts, str) else type_.contexts
            for context in contexts_:
                if self.context_sets.get(context) is None:
                    self.context_sets[context] = set()
                for ext in type_.exts:
                    self.context_sets[context].add(ext)

    def contains(self, ext: str, context: str) -> bool:
        equivalent_exts = MediaTypes.equivalent_exts.get(ext) or [ext]
        return any(e in self.context_sets.get(context, []) for e in equivalent_exts)


class MediaTypes(metaclass=SanitizedAttr):
    _all_groups: list[MediaTypeGroup] = []
    _chained_groups: dict[str, set[str]] = {}
    _name_to_key_map: dict[str, str] = {}
    equivalent_exts: dict[str, set[str]] = {}

    @classmethod
    def add_name_aliases(cls, group_key: str, names: str | list[str]) -> None:
        """Adds one or more aliases for the proper name of a group.

        If a group with the group_key does not exist, it will be created.

        For example, "Adobe" and "Adobe Photoshop" would be proper group names.
        """
        group = getattr(MediaTypes, group_key, None)
        if group is None:
            cls.register(group_key, [], [])
            group = getattr(MediaTypes, group_key, None)

        if not isinstance(group, MediaTypeGroup):
            return

        if isinstance(names, str):
            names = [names]
        for name in names:
            group.name_aliases.append(name)
            # Map the name and common variants of the name to the group key.
            cls._name_to_key_map[name] = group_key
            cls._name_to_key_map[name.lower()] = group_key
            cls._name_to_key_map[
                name.lower().replace(" ", "").replace("-", "").replace("_", "")
            ] = group_key
            cls._name_to_key_map[name.replace(" ", "").replace("-", "").replace("_", "")] = (
                group_key
            )

    @classmethod
    def get_group_key_from_name(
        cls, name: str, case_sensitive: bool = True, ignore_whitespace: bool = False
    ) -> str | None:
        """Attempt to return a group key given a proper name for the group."""
        if not case_sensitive:
            name = name.lower()
        if ignore_whitespace:
            name = name.replace(" ", "").replace("-", "").replace("_", "")
        return cls._name_to_key_map.get(name)

    @classmethod
    def register(cls, name: str, ext: list[str] | str, contexts: list[str] | str) -> None:
        # Sanitize and homogenize arguments
        attr_name = name.replace(".", "_")
        if isinstance(ext, str):
            ext = [ext]
        if isinstance(contexts, str):
            contexts = [contexts]

        # Check for existing group or create new one
        group = getattr(MediaTypes, attr_name, None)
        assert isinstance(group, MediaTypeGroup) or group is None

        if group is None:
            logger.debug(f"[MediaTypes] Creating Group: '{attr_name}' with {ext}")
            group = MediaTypeGroup(name, [])
            group.add_types([MediaType(ext, contexts)])
            setattr(MediaTypes, attr_name, group)
            cls._all_groups.append(group)
        else:
            logger.debug(f"[MediaTypes] Amending Group: '{attr_name}' with {ext}")
            group.add_types([MediaType(ext, contexts)])

        # Store any file extention equivalents
        if len(ext) > 1:
            for e in ext:
                existing_ext = cls.equivalent_exts.get(e)
                if existing_ext is None:
                    cls.equivalent_exts[e] = set(ext)

        # Create any chained groups from dot notations (e.g. "adobe.photoshop")
        name_parts = name.split(".")
        for i in range(1, len(name_parts)):
            parent = ".".join(name_parts[:i])
            child = ".".join(name_parts[: i + 1])
            cls.chain_group(parent, [child])

        # Update any chained groups
        chained_groups: set[str] = set()
        for k, v in cls._chained_groups.items():
            if name in v:
                chained_groups.add(k)

        if chained_groups:
            for c_name in chained_groups:
                cls.register(c_name, ext, contexts)

    @classmethod
    def chain_group(cls, parent_group: str, child_groups: str | list[str]) -> None:
        """Chain groups so when a type is added to a child group it's also added to a parent group.

        Args:
            parent_group (str): The group that will also update whenever a child group is updated.
                If the group doesn't exist, it will be created.
            child_groups (str | list[str]): Groups that tell a parent group to update as well.
                If the group doesn't exist, it will be created.
        """
        if isinstance(child_groups, str):
            child_groups = [child_groups]

        # If the groups don't exist, register it.
        if getattr(MediaTypes, parent_group.replace(".", "_"), None) is None:
            cls.register(parent_group, [], [])
        for child_group in child_groups:
            if getattr(MediaTypes, child_group.replace(".", "_"), None) is None:
                cls.register(child_group, [], [])

        if cls._chained_groups.get(parent_group) is None:
            cls._chained_groups[parent_group] = set()

        for c_group in child_groups:
            cls._chained_groups[parent_group].add(c_group)

    @classmethod
    def find(cls, ext: str, context: str) -> list[MediaTypeGroup]:
        groups: list[MediaTypeGroup] = []
        for group in cls._all_groups:
            for type_ in group.types:
                equivalent_exts = cls.equivalent_exts.get(ext) or [ext]
                for e in equivalent_exts:
                    if e in type_.exts and context in type_.contexts:
                        groups.append(group)
                        break

        return groups

    @classmethod
    def get_equivalent_exts(cls, ext: str) -> set[str]:
        """Return a set of equivalent file extensions given an extention, including itself.

        Args:
            ext (str): The file extension, including leading dot.
        """
        return cls.equivalent_exts.get(ext, {ext})


# Vendor.Suite.Product =============================================================================
# These groups are designed so that searching for either the vendor, suite, or product
# will return file types only under that group level.

# Initial Miscellaneous Chaining ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
MediaTypes.chain_group(
    "office",
    [
        "adobe.acrobat",
        "apple.iwork",
        "microsoft.office",
        "open_document",
    ],
)
MediaTypes.chain_group(
    "document",
    [
        "adobe.acrobat",
        "apple.iwork.pages",
        "microsoft.office.word",
        "open_document.document",
        "typesetting",
    ],
)
MediaTypes.chain_group(
    "presentation",
    [
        "apple.iwork.keynote",
        "microsoft.office.powerpoint",
        "open_document.presentation",
    ],
)
MediaTypes.chain_group(
    "spreadsheet",
    [
        "apple.iwork.numbers",
        "microsoft.office.excel",
        "open_document.spreadsheet",
    ],
)

# Adobe ------------------------------------------------------------------------
MediaTypes.add_name_aliases("adobe", "Adobe")

# Adobe Acrobat/Reader
MediaTypes.add_name_aliases(
    "adobe.acrobat",
    [
        "Acrobat",
        "Adobe Acrobat",
        "Adobe Reader",
        "PDF",
        "Reader",
    ],
)
MediaTypes.register("adobe.acrobat", ".fdf", SEARCH)
MediaTypes.register("adobe.acrobat", ".pdf", SEARCH)
MediaTypes.register("adobe.acrobat", ".pdx", SEARCH)
MediaTypes.register("adobe.acrobat", ".ps", SEARCH)
MediaTypes.register("adobe.acrobat", ".xfdf", SEARCH)
MediaTypes.register("adobe.acrobat", ".xps", SEARCH)

# Adobe Illustrator
MediaTypes.add_name_aliases("adobe.illustrator", ["Illustrator", "Adobe Illustrator"])
MediaTypes.register("adobe.illustrator", ".ai", SEARCH)

# Adobe Photoshop
MediaTypes.add_name_aliases("adobe.photoshop", ["Photoshop", "Adobe Photoshop"])
MediaTypes.register("adobe.photoshop", ".pdd", SEARCH)
MediaTypes.register("adobe.photoshop", ".psb", SEARCH)
MediaTypes.register("adobe.photoshop", ".psd", SEARCH)


# Affinity ---------------------------------------------------------------------
# NOTE: Affinity suite products with generic names (e.g. "Photo") should not have those
# names be standalone aliases as they will conflict with other, more common names.
MediaTypes.add_name_aliases("affinity", "Affinity")
MediaTypes.register("affinity", ".af", SEARCH)

# Affinity Designer
MediaTypes.add_name_aliases("affinity.designer", ["Designer", "Affinity Designer"])
MediaTypes.register("affinity.designer", ".afdesign", SEARCH)

# Affinity Photo
MediaTypes.add_name_aliases("affinity.photo", "Affinity Photo")
MediaTypes.register("affinity.photo", ".afphoto", SEARCH)

# Affinity Publisher
MediaTypes.add_name_aliases("affinity.publisher", "Affinity Publisher")
MediaTypes.register("affinity.publisher", [".afpublisher", ".afpub"], SEARCH)


# Apple & iWork ----------------------------------------------------------------
MediaTypes.add_name_aliases("apple", "Apple")
MediaTypes.add_name_aliases("apple.iwork", "iWork")
MediaTypes.add_name_aliases("apple.creator_studio", ["Apple Creator Studio", "Creator Studio"])
MediaTypes.chain_group("apple.creator_studio", "apple.iwork")  # iWork is a subset of Creator Studio

# Apple Books
MediaTypes.add_name_aliases("apple.books", ["Apple Books", "Apple iBooks", "iBooks"])
MediaTypes.register("apple.books", ".ibook", SEARCH)

# Keynote (iWork + Apple Creator Studio)
MediaTypes.add_name_aliases(
    "apple.iwork.keynote",
    [
        "Keynote",
        "Apple Keynote",
        "Apple iWork Keynote",
        "iWork Keynote",
    ],
)
MediaTypes.register("apple.iwork.keynote", ".key", SEARCH)

# Numbers (iWork + Apple Creator Studio)
MediaTypes.add_name_aliases(
    "apple.iwork.numbers",
    [
        "Numbers",
        "Apple Numbers",
        "Apple iWork Numbers",
        "iWork Numbers",
    ],
)
MediaTypes.register("apple.iwork.numbers", ".numbers", SEARCH)

# Pages (iWork + Apple Creator Studio)
MediaTypes.add_name_aliases(
    "apple.iwork.pages",
    [
        "Pages",
        "Apple Pages",
        "Apple iWork Pages",
        "iWork Pages",
    ],
)
MediaTypes.register("apple.iwork.pages", ".pages", SEARCH)

# Pixelmator Pro (Apple Creator Studio)
MediaTypes.add_name_aliases(
    "apple.creator_studio.pixelmator",
    [
        "Apple Pixelmator Pro",
        "Apple Pixelmator",
        "Pixelmator Pro",
        "Pixelmator",
    ],
)
MediaTypes.register("apple.creator_studio.pixelmator", ".pxd", SEARCH)


# Autodesk ---------------------------------------------------------------------
MediaTypes.add_name_aliases("autodesk", "Autodesk")
MediaTypes.register("autodesk", ".3ds", SEARCH)
MediaTypes.register("autodesk", ".fbx", SEARCH)


# Blender ----------------------------------------------------------------------
MediaTypes.add_name_aliases("blender", "Blender")
MediaTypes.register("blender", ".blen_tc", SEARCH)
MediaTypes.register("blender", ".blend", SEARCH)
# Numbered Blender auto-backup files (.blend1 - .blend32)
MediaTypes.register("blender", [f".blend{i}" for i in range(1, 33)], SEARCH)


# Clip Studio Paint ------------------------------------------------------------
MediaTypes.add_name_aliases("clip_studio_paint", ["Clip Studio", "Clip Studio Paint"])
MediaTypes.register("clip_studio_paint", ".clip", SEARCH)
MediaTypes.register("clip_studio_paint", ".cmc", SEARCH)
MediaTypes.register("clip_studio_paint", ".lip", SEARCH)


# Corel ------------------------------------------------------------------------
MediaTypes.add_name_aliases("corel.wordperfect", ["WordPerfect", "Corel WordPerfect"])
MediaTypes.register("corel.wordperfect", ".wpd", SEARCH)
MediaTypes.add_name_aliases("corel", "Corel")


# GIMP -------------------------------------------------------------------------
MediaTypes.add_name_aliases("gimp", "GIMP")
MediaTypes.register("gimp", ".ora", SEARCH)  # OpenRaster, used by Krita, GIMP, etc.
MediaTypes.register("gimp", ".xcf", SEARCH)


# Krita ------------------------------------------------------------------------
# NOTE: As more KDE apps potentially get added, this might need to go under a KDE group.
MediaTypes.add_name_aliases("krita", ["Krita", "KDE Krita"])
MediaTypes.register("krita", ".kra", SEARCH)
MediaTypes.register("krita", ".krz", SEARCH)
MediaTypes.register("krita", ".ora", SEARCH)  # OpenRaster, used by Krita, GIMP, etc.


# MediBang Paint / FireAlpaca --------------------------------------------------
MediaTypes.add_name_aliases("medibang_paint", ["FireAlpaca", "MediBang Paint", "MediBang"])
MediaTypes.register("medibang_paint", ".mdp", SEARCH)


# Microsoft Office -------------------------------------------------------------
MediaTypes.add_name_aliases(
    "microsoft.office",
    [
        "Microsoft 365",
        "Microsoft Office 365",
        "Microsoft Office",
        "MS Office",
        "Office 365",
    ],
)
MediaTypes.register("microsoft.office", ".wdb", SEARCH)  # Microsoft Works Database

MediaTypes.add_name_aliases(
    "microsoft.office.access",
    [
        "Access",
        "Microsoft Access",
        "Microsoft Office Access",
        "Office Access",
    ],
)
MediaTypes.register("microsoft.office.access", ".accdb", SEARCH)
MediaTypes.register("microsoft.office.access", ".mdb", SEARCH)

MediaTypes.add_name_aliases(
    "microsoft.office.excel",
    [
        "Excel",
        "Microsoft Excel",
        "Microsoft Office Excel",
        "Office Excel",
    ],
)
MediaTypes.register("microsoft.office.excel", ".xlr", SEARCH)
MediaTypes.register("microsoft.office.excel", ".xls", SEARCH)
MediaTypes.register("microsoft.office.excel", ".xlsx", SEARCH)

MediaTypes.add_name_aliases(
    "microsoft.office.powerpoint",
    [
        "PowerPoint",
        "Microsoft PowerPoint",
        "Microsoft Office PowerPoint",
        "Office PowerPoint",
    ],
)
MediaTypes.register("microsoft.office.powerpoint", ".pot", SEARCH)
MediaTypes.register("microsoft.office.powerpoint", ".potm", SEARCH)
MediaTypes.register("microsoft.office.powerpoint", ".potx", SEARCH)
MediaTypes.register("microsoft.office.powerpoint", ".ppam", SEARCH)
MediaTypes.register("microsoft.office.powerpoint", ".pps", SEARCH)
MediaTypes.register("microsoft.office.powerpoint", ".ppsm", SEARCH)
MediaTypes.register("microsoft.office.powerpoint", ".ppsx", SEARCH)
MediaTypes.register("microsoft.office.powerpoint", ".ppt", SEARCH)
MediaTypes.register("microsoft.office.powerpoint", ".pptm", SEARCH)
MediaTypes.register("microsoft.office.powerpoint", ".pptx", SEARCH)


MediaTypes.add_name_aliases(
    "microsoft.office.word",
    [
        "Word",
        "Microsoft Word",
        "Microsoft Office Word",
        "Office Word",
    ],
)
MediaTypes.register("microsoft.office.word", ".doc", SEARCH)
MediaTypes.register("microsoft.office.word", ".docm", SEARCH)
MediaTypes.register("microsoft.office.word", ".docx", SEARCH)
MediaTypes.register("microsoft.office.word", ".dot", SEARCH)
MediaTypes.register("microsoft.office.word", ".dotm", SEARCH)
MediaTypes.register("microsoft.office.word", ".dotx", SEARCH)
MediaTypes.register("microsoft.office.word", ".wps", SEARCH)


# MuseScore --------------------------------------------------------------------
MediaTypes.add_name_aliases("musescore", ["MuseScore", "MuseScore Studio"])
MediaTypes.register("musescore", ".mscz", SEARCH)


# OpenDocument -----------------------------------------------------------------
MediaTypes.add_name_aliases("open_document", ["LibreOffice", "OpenDocument", "OpenOffice"])
MediaTypes.register("open_document", ".fodg", SEARCH)
MediaTypes.register("open_document", ".odf", SEARCH)
MediaTypes.register("open_document", ".odg", SEARCH)

MediaTypes.register("open_document.document", ".fodt", SEARCH)
MediaTypes.register("open_document.document", ".odt", SEARCH)

MediaTypes.register("open_document.presentation", ".fodp", SEARCH)
MediaTypes.register("open_document.presentation", ".odp", SEARCH)

MediaTypes.register("open_document.spreadsheet", ".fods", SEARCH)
MediaTypes.register("open_document.spreadsheet", ".ods", SEARCH)


# Paint.NET --------------------------------------------------------------------
MediaTypes.add_name_aliases("paint_dot_net", ["Paint.NET", "PaintDotNet"])
MediaTypes.register("paint_dot_net", ".pdn", SEARCH)


# Valve Source Engine ----------------------------------------------------------
MediaTypes.add_name_aliases(
    "source_engine",
    [
        "Source 2 Engine",
        "Source Engine",
        "Valve Source 2 Engine",
        "Valve Source Engine",
    ],
)
MediaTypes.register("source_engine", ".fgd", SEARCH)
MediaTypes.register("source_engine", ".gi", SEARCH)
MediaTypes.register("source_engine", ".kv3", SEARCH)
MediaTypes.register("source_engine", ".nut", SEARCH)
MediaTypes.register("source_engine", ".vcfg", SEARCH)
MediaTypes.register("source_engine", ".vdf", SEARCH)
MediaTypes.register("source_engine", ".vmt", SEARCH)
MediaTypes.register("source_engine", ".vqlayout", SEARCH)
MediaTypes.register("source_engine", ".vsc", SEARCH)
MediaTypes.register("source_engine", ".vsnd_template", SEARCH)
MediaTypes.register("source_engine", ".vtf", SEARCH)

# General Media Types ==============================================================================
# These are general groups for media types based on the file formats and uses themselves, rather
# than the vendors. Extensions may be duplicated here if they belong in both sections.

# 3D Models & Materials --------------------------------------------------------
MediaTypes.add_name_aliases("material", "Material")
MediaTypes.register("material", ".mtl", SEARCH)

MediaTypes.add_name_aliases("model", ["3D Model", "3D Object", "Model", "Object"])
MediaTypes.register("model", ".3ds", SEARCH)
MediaTypes.register("model", ".3mf", SEARCH)
MediaTypes.register("model", ".fbx", SEARCH)
MediaTypes.register("model", ".obj", SEARCH)
MediaTypes.register("model", ".stl", SEARCH)

# Archives ---------------------------------------------------------------------
MediaTypes.add_name_aliases("archive", ["Archive", "Compressed"])
MediaTypes.register("archive", ".cba", SEARCH)  # Also under "ebook.comic"

# RAR
MediaTypes.add_name_aliases(
    "archive.rar",
    [
        "RAR Archive",
        "RAR",
        "WinRAR",
        "WinRAR Archive",
    ],
)
MediaTypes.register("archive.rar", ".cbr", SEARCH)  # Also under "ebook.comic"
MediaTypes.register("archive.rar", ".rar", SEARCH)
MediaTypes.register("archive.rar", ".rev", SEARCH)

# tar
MediaTypes.add_name_aliases(
    "archive.tar",
    [
        "Tape Archive",
        "tar Archive",
        "tarball",
        "tar",
    ],
)
MediaTypes.register("archive.tar", ".tar", SEARCH)
MediaTypes.register("archive.tar", [".tar.bz", ".tb2", ".tbz", ".tbz2", ".tz2"], SEARCH)
MediaTypes.register("archive.tar", [".tar.gz", ".taz", ".tgz"], SEARCH)
MediaTypes.register("archive.tar", [".tar.lzma", ".tlz"], SEARCH)
MediaTypes.register("archive.tar", [".tar.xz", ".txz"], SEARCH)
MediaTypes.register("archive.tar", [".tar.zst", ".tzst"], SEARCH)
MediaTypes.register("archive.tar", ".cbt", SEARCH)  # Also under "ebook.comic"

# ZIP
MediaTypes.add_name_aliases(
    "archive.zip",
    [
        "7-Zip Archive",
        "7-Zip",
        "SevenZip Archive",
        "SevenZip",
        "WinZIP Archive",
        "WinZIP",
        "Zip Archive",
        "ZIP",
        "ZIP File",
    ],
)
MediaTypes.register("archive.zip", ".7z", SEARCH)
MediaTypes.register("archive.zip", ".cb7", SEARCH)  # Also under "ebook.comic"
MediaTypes.register("archive.zip", ".cbz", SEARCH)  # Also under "ebook.comic"
MediaTypes.register("archive.zip", ".gz", SEARCH)
MediaTypes.register("archive.zip", ".s7z", SEARCH)
MediaTypes.register("archive.zip", ".zip", SEARCH)
MediaTypes.register("archive.zip", ".zipx", SEARCH)


# Audio ------------------------------------------------------------------------
MediaTypes.add_name_aliases("audio", "Audio")
MediaTypes.register("audio", ".aac", SEARCH)
MediaTypes.register("audio", ".aifc", SEARCH)
MediaTypes.register("audio", ".caf", SEARCH)
MediaTypes.register("audio", ".flac", SEARCH)
MediaTypes.register("audio", ".m4a", SEARCH)
MediaTypes.register("audio", ".m4p", SEARCH)
MediaTypes.register("audio", ".mp3", SEARCH)
MediaTypes.register("audio", ".ogg", SEARCH)
MediaTypes.register("audio", ".wma", SEARCH)
MediaTypes.register("audio", [".aif", ".aiff"], SEARCH)
MediaTypes.register("audio", [".wav", ".wave"], SEARCH)

# MIDI
MediaTypes.add_name_aliases("audio.midi", ["MIDI", "General MIDI"])
MediaTypes.register("audio.midi", [".mid", ".midi"], SEARCH)


# Binary -----------------------------------------------------------------------
MediaTypes.add_name_aliases("binary", "Binary")
MediaTypes.register("binary", ".aab", SEARCH)
MediaTypes.register("binary", ".dll", SEARCH)
MediaTypes.register("binary", ".dylib", SEARCH)
MediaTypes.register("binary", ".exe", SEARCH)
MediaTypes.register("binary", ".o", SEARCH)
MediaTypes.register("binary", ".pyc", SEARCH)
MediaTypes.register("binary", ".pyd", SEARCH)
MediaTypes.register("binary", ".pyo", SEARCH)


# Databases --------------------------------------------------------------------
MediaTypes.add_name_aliases("database", ["Database", "DB"])
MediaTypes.register("database", ".db", SEARCH)
MediaTypes.register("database", ".pdb", SEARCH)
MediaTypes.register("database", ".sqlite", SEARCH)
MediaTypes.register("database", ".sqlite3", SEARCH)
MediaTypes.register("database", ".wdb", SEARCH)


# Documents --------------------------------------------------------------------
MediaTypes.add_name_aliases("document", ["Document", "Text Document", "Word Processor"])


# Disk Images ------------------------------------------------------------------
MediaTypes.add_name_aliases("disk_image", ["Disk Image", "Disc Image"])
MediaTypes.register("disk_image", ".bios", SEARCH)
MediaTypes.register("disk_image", ".dmg", SEARCH)
MediaTypes.register("disk_image", ".fhdx", SEARCH)
MediaTypes.register("disk_image", ".iso", SEARCH)
MediaTypes.register("disk_image", ".udf", SEARCH)


# eBooks & Comics --------------------------------------------------------------
MediaTypes.add_name_aliases("ebook", "eBook")
MediaTypes.register("ebook", ".azw", SEARCH)
MediaTypes.register("ebook", ".azw3", SEARCH)
MediaTypes.register("ebook", ".djvu", SEARCH)
MediaTypes.register("ebook", ".epub", SEARCH)
MediaTypes.register("ebook", ".fb2", SEARCH)
MediaTypes.register("ebook", ".ibook", SEARCH)  # Also under "apple.books"
MediaTypes.register("ebook", ".kfx", SEARCH)
MediaTypes.register("ebook", ".lit", SEARCH)
MediaTypes.register("ebook", ".mobi", SEARCH)
MediaTypes.register("ebook", ".prc", SEARCH)

# Comic Book Archives
MediaTypes.add_name_aliases("ebook.comic", ["Comic Archive", "Comic Book Archive", "Comic"])
MediaTypes.register("ebook.comic", ".cb7", SEARCH)
MediaTypes.register("ebook.comic", ".cba", SEARCH)
MediaTypes.register("ebook.comic", ".cbr", SEARCH)
MediaTypes.register("ebook.comic", ".cbt", SEARCH)
MediaTypes.register("ebook.comic", ".cbz", SEARCH)


# Fonts ------------------------------------------------------------------------
MediaTypes.add_name_aliases("font", "Font")
MediaTypes.register("font", ".fon", SEARCH)
MediaTypes.register("font", ".otf", SEARCH)
MediaTypes.register("font", ".ttc", SEARCH)
MediaTypes.register("font", ".ttf", SEARCH)
MediaTypes.register("font", ".woff", SEARCH)
MediaTypes.register("font", ".woff2", SEARCH)


# Images -----------------------------------------------------------------------
MediaTypes.add_name_aliases("image", ["Image", "Photo", "Picture"])

# Raster Images
MediaTypes.add_name_aliases("image.raster", "Raster Image")
MediaTypes.register("image.raster", ".apng", SEARCH)
MediaTypes.register("image.raster", ".avif", SEARCH)
MediaTypes.register("image.raster", ".bmp", SEARCH)
MediaTypes.register("image.raster", ".exr", SEARCH)
MediaTypes.register("image.raster", ".gif", SEARCH)
MediaTypes.register("image.raster", [".jfif", ".jpeg_large", ".jpeg", ".jpg_large", ".jpg"], SEARCH)
MediaTypes.register("image.raster", ".jxl", SEARCH)
MediaTypes.register("image.raster", ".webp", SEARCH)
MediaTypes.register("image.raster", [".heic", ".heif"], SEARCH)
MediaTypes.register("image.raster", [".j2k", ".jp2", ".jpg2"], SEARCH)
MediaTypes.register("image.raster", [".tif", ".tiff"], SEARCH)

# Raw Images
MediaTypes.add_name_aliases("image.raster.raw", ["Digital Negative", "Raw Image", "Raw"])
MediaTypes.register("image.raster.raw", ".arw", SEARCH)
MediaTypes.register("image.raster.raw", ".cr2", SEARCH)
MediaTypes.register("image.raster.raw", ".cr3", SEARCH)
MediaTypes.register("image.raster.raw", ".crw", SEARCH)
MediaTypes.register("image.raster.raw", ".dng", SEARCH)
MediaTypes.register("image.raster.raw", ".nef", SEARCH)
MediaTypes.register("image.raster.raw", ".nrw", SEARCH)
MediaTypes.register("image.raster.raw", ".orf", SEARCH)
MediaTypes.register("image.raster.raw", ".r3d", SEARCH)
MediaTypes.register("image.raster.raw", ".raf", SEARCH)
MediaTypes.register("image.raster.raw", ".raw", SEARCH)
MediaTypes.register("image.raster.raw", ".rw2", SEARCH)
MediaTypes.register("image.raster.raw", ".srf", SEARCH)
MediaTypes.register("image.raster.raw", ".srf2", SEARCH)

# Vector Images
MediaTypes.add_name_aliases(
    "image.vector",
    [
        "Scalable Vector Graphic",
        "Scalable Vector",
        "Vector Graphic",
        "Vector Image",
        "Vector",
    ],
)
MediaTypes.register("image.vector", ".eps", SEARCH)
MediaTypes.register("image.vector", ".epsf", SEARCH)
MediaTypes.register("image.vector", ".epsi", SEARCH)
MediaTypes.register("image.vector", ".svg", SEARCH)
MediaTypes.register("image.vector", ".svgz", SEARCH)

# Animated Images
MediaTypes.add_name_aliases("image.animated", ["Animated Image", "Animated"])
MediaTypes.register("image.animated", ".gif", SEARCH)
MediaTypes.register("image.animated", ".apng", SEARCH)
MediaTypes.register("image.animated", ".webp", SEARCH)
MediaTypes.register("image.animated", ".jxl", SEARCH)


# Presentations ----------------------------------------------------------------
MediaTypes.add_name_aliases("presentation", ["Presentation", "Slide Show"])
MediaTypes.register("presentation", ".fodp", SEARCH)
MediaTypes.register("presentation", ".key", SEARCH)
MediaTypes.register("presentation", ".odp", SEARCH)
MediaTypes.register("presentation", ".pot", SEARCH)
MediaTypes.register("presentation", ".potm", SEARCH)
MediaTypes.register("presentation", ".potx", SEARCH)
MediaTypes.register("presentation", ".ppam", SEARCH)
MediaTypes.register("presentation", ".pps", SEARCH)
MediaTypes.register("presentation", ".ppsm", SEARCH)
MediaTypes.register("presentation", ".ppsx", SEARCH)
MediaTypes.register("presentation", ".ppt", SEARCH)
MediaTypes.register("presentation", ".pptm", SEARCH)
MediaTypes.register("presentation", ".pptx", SEARCH)


# Programs, Installers, & Packages ---------------------------------------------
MediaTypes.add_name_aliases("program", ["App", "Application", "Executable", "Program"])
MediaTypes.register("program", ".apk", SEARCH)
MediaTypes.register("program", ".apkm", SEARCH)
MediaTypes.register("program", ".apks", SEARCH)
MediaTypes.register("program", ".app", SEARCH)
MediaTypes.register("program", ".appx", SEARCH)
MediaTypes.register("program", ".bin", SEARCH)
MediaTypes.register("program", ".exe", SEARCH)
MediaTypes.register("program", ".msi", SEARCH)
MediaTypes.register("program", ".msix", SEARCH)
MediaTypes.register("program", ".pkg", SEARCH)
MediaTypes.register("program", ".xapk", SEARCH)


# Rich Text --------------------------------------------------------------------
MediaTypes.add_name_aliases("rich_text", ["Rich Text", "Rich Text Document"])
MediaTypes.register("rich_text", ".rtf", SEARCH)


# Shaders ----------------------------------------------------------------------
MediaTypes.add_name_aliases("shader", "Shader")
MediaTypes.register("shader", ".effect", SEARCH)
MediaTypes.register("shader", ".frag", SEARCH)
MediaTypes.register("shader", ".fsh", SEARCH)
MediaTypes.register("shader", ".glsl", SEARCH)
MediaTypes.register("shader", ".shader", SEARCH)
MediaTypes.register("shader", ".vert", SEARCH)
MediaTypes.register("shader", ".vsh", SEARCH)

# Shell Script -----------------------------------------------------------------
MediaTypes.add_name_aliases("shell", ["Shell Script", "Shell"])
MediaTypes.register("shell", ".bat", SEARCH)
MediaTypes.register("shell", ".csh", SEARCH)
MediaTypes.register("shell", ".fish", SEARCH)
MediaTypes.register("shell", ".nu", SEARCH)
MediaTypes.register("shell", ".ps1", SEARCH)
MediaTypes.register("shell", ".sh", SEARCH)
MediaTypes.register("shell", "activate", SEARCH)


# Shortcuts --------------------------------------------------------------------
MediaTypes.add_name_aliases("shortcut", "Shortcut")
MediaTypes.register("shortcut", ".desktop", SEARCH)
MediaTypes.register("shortcut", ".lnk", SEARCH)
MediaTypes.register("shortcut", ".url", SEARCH)


# Spreadsheets -----------------------------------------------------------------
MediaTypes.add_name_aliases("spreadsheet", ["Spreadsheet", "Sheet"])
MediaTypes.register("spreadsheet", ".csv", SEARCH)

# Plaintext --------------------------------------------------------------------
# NOTE: If extensions here can be grouped or moved to more specific categories, do that.
# Something like a "Code" group may be considered, but that may be too subjective.

MediaTypes.add_name_aliases("plaintext", "Plaintext")
MediaTypes.register("plaintext", ".cfg", SEARCH)
MediaTypes.register("plaintext", ".conf", SEARCH)
MediaTypes.register("plaintext", ".config", SEARCH)
MediaTypes.register("plaintext", ".i3u", SEARCH)
MediaTypes.register("plaintext", ".lang", SEARCH)
MediaTypes.register("plaintext", ".lock", SEARCH)
MediaTypes.register("plaintext", ".log", SEARCH)
MediaTypes.register("plaintext", ".plist", SEARCH)
MediaTypes.register("plaintext", ".theme", SEARCH)
MediaTypes.register("plaintext", "contributing", SEARCH)
MediaTypes.register("plaintext", "license", SEARCH)
MediaTypes.register("plaintext", "readme", SEARCH)
MediaTypes.register("plaintext", [".editorconfig", ".inf", ".ini"], SEARCH)
MediaTypes.register("plaintext", [".txt", ".text"], SEARCH)
MediaTypes.register("plaintext", ["pkginfo", ".pkginfo"], SEARCH)

# CSS
MediaTypes.add_name_aliases("plaintext.css", "CSS")
MediaTypes.register("plaintext.css", ".css", SEARCH)
MediaTypes.register("plaintext.css", ".less", SEARCH)
MediaTypes.register("plaintext.css", ".qss", SEARCH)
MediaTypes.register("plaintext.css", ".sass", SEARCH)
MediaTypes.register("plaintext.css", ".scss", SEARCH)
MediaTypes.register("plaintext.css", ".styl", SEARCH)

# HTML
MediaTypes.add_name_aliases("plaintext.html", "HTML")
MediaTypes.register("plaintext.html", [".dhtml", ".htm", ".html", ".shtml", ".xhtml"], SEARCH)

# JavaScript
MediaTypes.chain_group("plaintext.javascript", "plaintext.typescript")
MediaTypes.add_name_aliases("plaintext.javascript", ["JavaScript", "JS"])
MediaTypes.register("plaintext.javascript", ".cjs", SEARCH)
MediaTypes.register("plaintext.javascript", ".js", SEARCH)
MediaTypes.register("plaintext.javascript", ".jsx", SEARCH)
MediaTypes.register("plaintext.javascript", ".mjs", SEARCH)

# JSON
MediaTypes.add_name_aliases("plaintext.json", "JSON")
MediaTypes.register("plaintext.json", [".json", ".json5", ".jsonc", ".jsonl"], SEARCH)

# Markdown
MediaTypes.add_name_aliases("plaintext.markdown", ["Markdown", "MD"])
MediaTypes.register("plaintext.markdown", [".markdown", ".md", ".mkd", ".rmd"], SEARCH)

# TOML
MediaTypes.add_name_aliases("plaintext.toml", "TOML")
MediaTypes.register("plaintext.toml", ".toml", SEARCH)

# TypeScript
MediaTypes.add_name_aliases("plaintext.typescript", "TypeScript")
MediaTypes.register("plaintext.typescript", ".cts", SEARCH)
MediaTypes.register("plaintext.typescript", ".ts", SEARCH)
MediaTypes.register("plaintext.typescript", ".mts", SEARCH)
MediaTypes.register("plaintext.typescript", ".tsx", SEARCH)

# XML
MediaTypes.add_name_aliases("plaintext.xml", "XML")
MediaTypes.register("plaintext.xml", [".xml", ".xul"], SEARCH)

# YAML
MediaTypes.add_name_aliases("plaintext.yaml", "YAML")
MediaTypes.register("plaintext.yaml", [".yaml", ".yml"], SEARCH)


# Python -----------------------------------------------------------------------
MediaTypes.add_name_aliases("python", "Python")
MediaTypes.register("python", ".ipynb", SEARCH)
MediaTypes.register("python", ".py", SEARCH)
MediaTypes.register("python", ".pyc", SEARCH)
MediaTypes.register("python", ".pyd", SEARCH)
MediaTypes.register("python", ".pyi", SEARCH)
MediaTypes.register("python", ".pyo", SEARCH)


# Typesetting ------------------------------------------------------------------
MediaTypes.add_name_aliases("typesetting", ["Typesetting", "Typesetter"])

# TeX/LaTeX
MediaTypes.add_name_aliases("typesetting.latex", ["LaTeX", "TeX"])
MediaTypes.register("typesetting.latex", ".tex", SEARCH)

# Typst
MediaTypes.add_name_aliases("typesetting.typst", "Typst")
MediaTypes.register("typesetting.typst", ".typ", SEARCH)


# Video ------------------------------------------------------------------------
MediaTypes.add_name_aliases("video", "Video")
MediaTypes.register("video", ".3gp", SEARCH)
MediaTypes.register("video", ".avi", SEARCH)
MediaTypes.register("video", ".flv", SEARCH)
MediaTypes.register("video", ".gifv", SEARCH)
MediaTypes.register("video", ".hevc", SEARCH)
MediaTypes.register("video", ".m4p", SEARCH)
MediaTypes.register("video", ".m4v", SEARCH)
MediaTypes.register("video", ".mkv", SEARCH)
MediaTypes.register("video", ".mov", SEARCH)
MediaTypes.register("video", ".mp4", SEARCH)
MediaTypes.register("video", ".webm", SEARCH)
MediaTypes.register("video", ".wmv", SEARCH)


@deprecated("Use the new MediaTypes system.")
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


@deprecated("Use the new MediaTypes system.")
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


@deprecated("Use the new MediaTypes system.")
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
