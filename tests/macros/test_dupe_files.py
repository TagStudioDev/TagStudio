# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


from pathlib import Path

from tagstudio.core.library.alchemy.fields import BaseField, TextField
from tagstudio.core.library.alchemy.library import Library
from tagstudio.core.library.alchemy.models import Entry
from tagstudio.core.library.alchemy.registries.dupe_files_registry import DupeFilesRegistry

CWD = Path(__file__).parent


def test_refresh_dupe_files(library: Library):
    library.library_dir = Path("/tmp/")

    fields: list[BaseField] = [TextField(name="Title", value="I'm a Test Title")]

    entry = Entry(
        path=Path("bar/foo.txt"),
        fields=fields,
    )

    entry2 = Entry(
        path=Path("foo/foo.txt"),
        fields=fields,
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
