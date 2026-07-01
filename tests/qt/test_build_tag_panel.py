# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


from collections.abc import Callable

from pytestqt.qtbot import QtBot

from tagstudio.core.library.alchemy.library import Library
from tagstudio.core.library.alchemy.models import Tag, TagAlias
from tagstudio.core.utils.types import unwrap
from tagstudio.qt.mixed.build_tag import BuildTagPanel, CustomTableItem
from tagstudio.qt.translations import Translations


def test_build_tag_panel_add_sub_tag_callback(
    qtbot: QtBot, library: Library, generate_tag: Callable[..., Tag]
):
    parent = unwrap(library.add_tag(generate_tag("xxx", id=123)))
    child = unwrap(library.add_tag(generate_tag("xx", id=124)))

    panel: BuildTagPanel = BuildTagPanel(library, child)
    qtbot.addWidget(panel)

    panel._add_parent_tag_callback(parent.id)  # pyright: ignore[reportPrivateUsage]

    assert len(panel.parent_ids) == 1


def test_build_tag_panel_remove_subtag_callback(
    qtbot: QtBot, library: Library, generate_tag: Callable[..., Tag]
):
    parent = unwrap(library.add_tag(generate_tag("xxx", id=123)))
    child = unwrap(library.add_tag(generate_tag("xx", id=124)))

    library.update_tag(child, {parent.id}, [])

    child = unwrap(library.get_tag(child.id))

    panel: BuildTagPanel = BuildTagPanel(library, child)
    qtbot.addWidget(panel)

    panel._remove_parent_tag_callback(parent.id)  # pyright: ignore[reportPrivateUsage]

    assert len(panel.parent_ids) == 0


import os

os.environ["QT_QPA_PLATFORM"] = "offscreen"


def test_build_tag_panel_add_alias_callback(
    qtbot: QtBot, library: Library, generate_tag: Callable[..., Tag]
):
    tag = unwrap(library.add_tag(generate_tag("xxx", id=123)))

    panel: BuildTagPanel = BuildTagPanel(library, tag)
    qtbot.addWidget(panel)

    panel._create_alias_callback()  # pyright: ignore[reportPrivateUsage]

    assert panel.aliases_table.rowCount() == 1


def test_build_tag_panel_remove_alias_callback(
    qtbot: QtBot, library: Library, generate_tag: Callable[..., Tag]
):
    tag: Tag = unwrap(library.add_tag(generate_tag("xxx", id=123)))

    alias_1 = TagAlias("alias", tag.id)
    alias_2 = TagAlias("alias_2", tag.id)
    library.update_tag(tag, [], {alias_1, alias_2})

    tag = unwrap(library.get_tag(tag.id))

    assert "alias" in tag.alias_strings
    assert "alias_2" in tag.alias_strings

    panel: BuildTagPanel = BuildTagPanel(library, tag)
    qtbot.addWidget(panel)

    alias: TagAlias = unwrap(library.get_alias(tag.id, tag.alias_ids[0]))
    panel.remove_alias_callback(alias)

    assert len(panel.aliases) == 1
    assert alias not in panel.aliases
    assert (alias.id, alias.name) not in [(a.id, a.name) for a in panel.aliases]


def test_build_tag_panel_set_parent_tags(
    qtbot: QtBot, library: Library, generate_tag: Callable[..., Tag]
):
    parent = unwrap(library.add_tag(generate_tag("parent", id=123)))
    child = unwrap(library.add_tag(generate_tag("child", id=124)))

    library.add_parent_tag(parent.id, child.id)

    child = library.get_tag(child.id)

    panel: BuildTagPanel = BuildTagPanel(library, child)
    qtbot.addWidget(panel)

    assert len(panel.parent_ids) == 1
    assert panel.parent_tags_scroll_layout.count() == 1


def test_build_tag_panel_add_aliases(
    qtbot: QtBot, library: Library, generate_tag: Callable[..., Tag]
):
    tag: Tag = unwrap(library.add_tag(generate_tag("xxx", id=123)))

    alias_1 = TagAlias("alias", tag.id)
    alias_2 = TagAlias("alias_2", tag.id)
    library.update_tag(tag, [], {alias_1, alias_2})

    tag = unwrap(library.get_tag(tag.id))

    assert "alias" in tag.alias_strings
    assert "alias_2" in tag.alias_strings

    panel: BuildTagPanel = BuildTagPanel(library, tag)
    qtbot.addWidget(panel)

    widget = panel.aliases_table.cellWidget(0, 1)
    assert isinstance(widget, CustomTableItem)

    alias_names: set[str] = set()
    alias_names.add(widget.text())

    widget = panel.aliases_table.cellWidget(1, 1)
    assert isinstance(widget, CustomTableItem)
    alias_names.add(widget.text())

    assert "alias" in alias_names
    assert "alias_2" in alias_names


def test_build_tag_panel_set_aliases(
    qtbot: QtBot, library: Library, generate_tag: Callable[..., Tag]
):
    tag: Tag = unwrap(library.add_tag(generate_tag("xxx", id=123)))
    alias_1 = TagAlias("Alias 1", tag.id)
    library.update_tag(tag, [], [alias_1])

    tag = unwrap(library.get_tag(tag.id))

    assert len(tag.alias_ids) == 1

    panel: BuildTagPanel = BuildTagPanel(library, tag)
    qtbot.addWidget(panel)

    assert panel.aliases_table.rowCount() == 1
    assert len(panel.aliases) == 1


def test_build_tag_panel_set_tag(qtbot: QtBot, library: Library, generate_tag: Callable[..., Tag]):
    tag = unwrap(library.add_tag(generate_tag("xxx", id=123)))

    panel: BuildTagPanel = BuildTagPanel(library, tag)
    qtbot.addWidget(panel)

    assert unwrap(panel.tag).name == "xxx"


def test_build_tag_panel_build_tag(qtbot: QtBot, library: Library):
    panel: BuildTagPanel = BuildTagPanel(library)
    qtbot.addWidget(panel)

    tag: Tag = panel.build_tag()

    assert tag.name == Translations["tag.new"]
