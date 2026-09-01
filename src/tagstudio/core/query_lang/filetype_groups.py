# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: MIT


import structlog

from tagstudio.core.media_types import MediaTypes

logger = structlog.get_logger(__name__)


SEARCH = "SEARCH"  # MediaType Context

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
MediaTypes.add_name_aliases("office", ["Office", "Office Suite"])

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

# Unity Game Engine ------------------------------------------------------------
MediaTypes.add_name_aliases("unity", ["Unity Engine", "Unity"])
MediaTypes.register("unity", ".meta", SEARCH)

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
MediaTypes.register("audio", ".alac", SEARCH)
MediaTypes.register("audio", ".caf", SEARCH)
MediaTypes.register("audio", ".flac", SEARCH)
MediaTypes.register("audio", ".m4a", SEARCH)
MediaTypes.register("audio", ".m4p", SEARCH)
MediaTypes.register("audio", ".m4r", SEARCH)
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
MediaTypes.register("image.raster", ".jxl", SEARCH)
MediaTypes.register("image.raster", ".png", SEARCH)
MediaTypes.register("image.raster", ".webp", SEARCH)
MediaTypes.register("image.raster", [".heic", ".heif"], SEARCH)
MediaTypes.register("image.raster", [".j2k", ".jp2", ".jpg2"], SEARCH)
MediaTypes.register("image.raster", [".jfif", ".jpeg_large", ".jpeg", ".jpg_large", ".jpg"], SEARCH)
MediaTypes.register("image.raster", [".tif", ".tiff"], SEARCH)

# Icons
MediaTypes.add_name_aliases("image.raster.icon", "Icon")
MediaTypes.register("image.raster.icon", ".icns", SEARCH)
MediaTypes.register("image.raster.icon", ".ico", SEARCH)
MediaTypes.register("image.raster.icon", ".icon", SEARCH)

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
MediaTypes.register("plaintext", ".gitignore", SEARCH)
MediaTypes.register("plaintext", ".i3u", SEARCH)
MediaTypes.register("plaintext", ".lang", SEARCH)
MediaTypes.register("plaintext", ".lock", SEARCH)
MediaTypes.register("plaintext", ".log", SEARCH)
MediaTypes.register("plaintext", ".plist", SEARCH)
MediaTypes.register("plaintext", ".prefs", SEARCH)
MediaTypes.register("plaintext", ".spec", SEARCH)
MediaTypes.register("plaintext", ".theme", SEARCH)
MediaTypes.register("plaintext", ".timestamp", SEARCH)
MediaTypes.register("plaintext", "contributing", SEARCH)
MediaTypes.register("plaintext", "license", SEARCH)
MediaTypes.register("plaintext", "readme", SEARCH)
MediaTypes.register("plaintext", [".editorconfig", ".inf", ".ini"], SEARCH)
MediaTypes.register("plaintext", [".txt", ".text"], SEARCH)
MediaTypes.register("plaintext", ["pkginfo", ".pkginfo"], SEARCH)

# C
MediaTypes.add_name_aliases("plaintext.c", "C")
MediaTypes.register("plaintext.c", ".c", SEARCH)
MediaTypes.register("plaintext.c", ".h", SEARCH)

# C++
MediaTypes.add_name_aliases("plaintext.cpp", ["C++", "CPP"])
MediaTypes.register("plaintext.cpp", ".cpp", SEARCH)
MediaTypes.register("plaintext.cpp", ".h", SEARCH)
MediaTypes.register("plaintext.cpp", ".hpp", SEARCH)

# C#
MediaTypes.add_name_aliases("plaintext.csharp", ["C#", "C Sharp"])
MediaTypes.register("plaintext.csharp", ".cs", SEARCH)

# CSS
MediaTypes.add_name_aliases("plaintext.css", "CSS")
MediaTypes.register("plaintext.css", ".css", SEARCH)
MediaTypes.register("plaintext.css", ".less", SEARCH)
MediaTypes.register("plaintext.css", ".qss", SEARCH)
MediaTypes.register("plaintext.css", ".sass", SEARCH)
MediaTypes.register("plaintext.css", ".scss", SEARCH)
MediaTypes.register("plaintext.css", ".styl", SEARCH)

# D
MediaTypes.add_name_aliases("plaintext.d", "D")
MediaTypes.register("plaintext.d", ".d", SEARCH)
MediaTypes.register("plaintext.d", ".h", SEARCH)

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

# Lua
MediaTypes.add_name_aliases("plaintext.lua", "Lua")
MediaTypes.register("plaintext.lua", ".lua", SEARCH)

# Markdown
MediaTypes.add_name_aliases("plaintext.markdown", ["Markdown", "MD"])
MediaTypes.register("plaintext.markdown", [".markdown", ".md", ".mkd", ".rmd"], SEARCH)

# Nix
MediaTypes.add_name_aliases("plaintext.nix", "Nix")
MediaTypes.register("plaintext.nix", ".nix", SEARCH)

# PHP
MediaTypes.add_name_aliases("plaintext.php", "PHP")
MediaTypes.register("plaintext.php", ".php", SEARCH)

# Qt
MediaTypes.add_name_aliases("plaintext.qt", "Qt")
MediaTypes.register("plaintext.qt", ".qml", SEARCH)
MediaTypes.register("plaintext.qt", ".qrc", SEARCH)

# Rust
MediaTypes.add_name_aliases("plaintext.rust", "Rust")
MediaTypes.register("plaintext.rust", ".rs", SEARCH)

# Tcl
MediaTypes.add_name_aliases("plaintext.tcl", "Tcl")
MediaTypes.register("plaintext.tcl", ".tcl", SEARCH)

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
MediaTypes.register("python", ".sip", SEARCH)


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
MediaTypes.register("video", ".m4v", SEARCH)
MediaTypes.register("video", ".mkv", SEARCH)
MediaTypes.register("video", ".mov", SEARCH)
MediaTypes.register("video", ".mp4", SEARCH)
MediaTypes.register("video", ".webm", SEARCH)
MediaTypes.register("video", ".wmv", SEARCH)
