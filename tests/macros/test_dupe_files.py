# Copyright (C) 2025
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio

from pathlib import Path

from tagstudio.core.library.alchemy.library import Library
from tagstudio.core.library.alchemy.models import Entry
from tagstudio.core.library.alchemy.registries.dupe_files_registry import DupeFilesRegistry
from tagstudio.core.utils.types import unwrap

CWD = Path(__file__).parent


def test_refresh_dupe_files(library: Library):
    library.library_dir = Path("/tmp/")
    folder = unwrap(library.folder)

    entry = Entry(
        folder=folder,
        path=Path("bar/foo.txt"),
        fields=library.default_fields,
    )

    entry2 = Entry(
        folder=folder,
        path=Path("foo/foo.txt"),
        fields=library.default_fields,
    )

    library.add_entries([entry, entry2])

    registry = DupeFilesRegistry(library=library)

    dupe_file_path = CWD.parent / "fixtures" / "result.dupeguru"
    registry.refresh_dupe_files(dupe_file_path)

    assert len(registry.groups) == 1
    paths = [entry.path for entry in registry.groups[0]]
    assert paths == [
        Path("bar/foo.txt"),
        Path("foo.txt"),
        Path("foo/foo.txt"),
    ]
