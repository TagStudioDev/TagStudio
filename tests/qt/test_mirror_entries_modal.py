# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


from pathlib import Path
from unittest.mock import Mock

from pytestqt.qtbot import QtBot

from tagstudio.core.library.alchemy.library import Library
from tagstudio.core.library.alchemy.registries.dupe_files_registry import DupeFilesRegistry
from tagstudio.qt.mixed.mirror_entries_modal import MirrorEntriesModal
from tagstudio.qt.translations import Translations


def _registry_with_groups(library: Library) -> DupeFilesRegistry:
    registry = DupeFilesRegistry(library=library)
    registry.groups = [list(library.get_entries_full([1, 2]))]
    return registry


def test_refresh_list_shows_entry_paths(qtbot: QtBot, library: Library) -> None:
    modal = MirrorEntriesModal(Mock(), _registry_with_groups(library))
    qtbot.addWidget(modal)

    modal.refresh_list()

    item_text = modal.model.item(0).text()
    assert item_text == f"foo.txt\n{Path('one/two/bar.md')}"
    assert "Entry" not in item_text


def test_mirror_entries_progress_label_uses_group_count(
    qtbot: QtBot, library: Library, monkeypatch
) -> None:
    labels: list[str] = []

    class FakeProgressWidget:
        def __init__(self, **kwargs) -> None:
            pass

        def setWindowTitle(self, title: str) -> None:  # noqa: N802
            pass

        def from_iterable_function(self, function, update_label_callback, *done_callbacks) -> None:
            labels.append(update_label_callback(0))

    monkeypatch.setattr(
        "tagstudio.qt.mixed.mirror_entries_modal.ProgressWidget", FakeProgressWidget
    )
    modal = MirrorEntriesModal(Mock(selected=[]), _registry_with_groups(library))
    qtbot.addWidget(modal)

    modal.mirror_entries()

    assert labels == [Translations.format("entries.mirror.label", idx=1, total=1)]
