# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


from pathlib import Path
from subprocess import CompletedProcess
from tempfile import TemporaryDirectory

import pytest

from tagstudio.core.constants import IGNORE_NAME
from tagstudio.core.library.alchemy.library import Library
from tagstudio.core.library.refresh import RefreshTracker
from tagstudio.core.utils.types import unwrap

CWD = Path(__file__).parent


@pytest.mark.parametrize("exclude_mode", [True, False])
@pytest.mark.parametrize("library", [TemporaryDirectory()], indirect=True)
def test_refresh_new_files(library: Library, exclude_mode: bool):
    library_dir = unwrap(library.library_dir)
    # Given
    registry = RefreshTracker(library=library)
    library.included_files.clear()
    (library_dir / "FOO.MD").touch()
    (library_dir / IGNORE_NAME).write_text("*.md" if exclude_mode else "*\n!*.md")

    # Test if the single file was added
    list(registry.refresh_dir(library_dir, force_internal_tools=True))
    assert set(registry.files_not_in_library) == set([Path(IGNORE_NAME), Path("FOO.MD")])


@pytest.mark.parametrize("library", [TemporaryDirectory()], indirect=True)
def test_refresh_multi_byte_filenames(library: Library):
    library_dir = unwrap(library.library_dir)
    # Given
    registry = RefreshTracker(library=library)
    library.included_files.clear()
    (library_dir / ".TagStudio").mkdir()
    (library_dir / "こんにちは.txt").touch()
    (library_dir / "em–dash.txt").touch()
    (library_dir / "apostrophe’.txt").touch()
    (library_dir / "umlaute äöü.txt").touch()

    # Test if all files were added with their correct names and without exceptions
    list(registry.refresh_dir(library_dir))
    assert Path("こんにちは.txt") in registry.files_not_in_library
    assert Path("em–dash.txt") in registry.files_not_in_library
    assert Path("apostrophe’.txt") in registry.files_not_in_library
    assert Path("umlaute äöü.txt") in registry.files_not_in_library


@pytest.mark.parametrize("library", [TemporaryDirectory()], indirect=True)
def test_refresh_falls_back_when_ripgrep_fails(library: Library, monkeypatch: pytest.MonkeyPatch):
    library_dir = unwrap(library.library_dir)
    registry = RefreshTracker(library=library)
    library.included_files.clear()
    (library_dir / ".TagStudio").mkdir()
    (library_dir / "new-file.txt").touch()

    monkeypatch.setattr("tagstudio.core.library.refresh.shutil.which", lambda _: "rg")
    monkeypatch.setattr(
        "tagstudio.core.library.refresh.silent_run",
        lambda *args, **kwargs: CompletedProcess(
            args=args, returncode=1, stdout="", stderr="rg failed"
        ),
    )

    list(registry.refresh_dir(library_dir))

    assert Path("new-file.txt") in registry.files_not_in_library
