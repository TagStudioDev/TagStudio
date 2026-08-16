# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only

# pyright: reportPrivateUsage = false

from collections.abc import Callable
from typing import cast

from PySide6.QtWidgets import QCheckBox
from pytestqt.qtbot import QtBot

from tagstudio.core.library.alchemy.library import Library
from tagstudio.core.library.alchemy.models import Tag, TagAlias
from tagstudio.core.utils.types import unwrap
from tagstudio.i18n.translations import Translations
from tagstudio.qt.mixed.build_tag import BuildTagPanel, CustomTableItem
from tagstudio.qt.mixed.tag_widget import TagWidget


def test_build_tag_panel_add_sub_tag_callback(
    qtbot: QtBot, library: Library, generate_tag: Callable[..., Tag]
):
    parent = unwrap(library.add_tag(generate_tag("xxx", id=123)))
    child = unwrap(library.add_tag(generate_tag("xx", id=124)))

    panel: BuildTagPanel = BuildTagPanel(library, child)
    qtbot.addWidget(panel)

    panel._add_parent_tag_callback(parent.id)

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

    panel._remove_parent_tag_callback(parent.id)

    assert len(panel.parent_ids) == 0


import os

os.environ["QT_QPA_PLATFORM"] = "offscreen"


def test_build_tag_panel_add_alias_callback(
    qtbot: QtBot, library: Library, generate_tag: Callable[..., Tag]
):
    tag = unwrap(library.add_tag(generate_tag("xxx", id=123)))

    panel: BuildTagPanel = BuildTagPanel(library, tag)
    qtbot.addWidget(panel)

    panel._create_alias_callback()

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


def test_build_tag_panel_show_category_from_parent(
    qtbot: QtBot, library: Library, generate_tag: Callable[..., Tag]
):
    parent = unwrap(library.add_tag(generate_tag("parent", id=123, is_category=True)))
    child = unwrap(library.add_tag(generate_tag("child", id=124, parent_tags={parent})))

    panel: BuildTagPanel = BuildTagPanel(library, child)
    qtbot.addWidget(panel)

    tag_widget = __find_category_tag_widget(panel)
    assert tag_widget is not None
    assert tag_widget.tag == parent


def test_build_tag_panel_show_category_from_grandparent(
    qtbot: QtBot, library: Library, generate_tag: Callable[..., Tag]
):
    grandparent = unwrap(library.add_tag(generate_tag("grandparent", id=122, is_category=True)))
    parent = unwrap(library.add_tag(generate_tag("parent", id=123, parent_tags={grandparent})))
    child = unwrap(library.add_tag(generate_tag("child", id=124, parent_tags={parent})))

    panel: BuildTagPanel = BuildTagPanel(library, child)
    qtbot.addWidget(panel)

    tag_widget = __find_category_tag_widget(panel)
    assert tag_widget is not None
    assert tag_widget.tag == grandparent


def test_build_tag_panel_add_category_through_parent(
    qtbot: QtBot, library: Library, generate_tag: Callable[..., Tag]
):
    parent = unwrap(library.add_tag(generate_tag("parent", id=123, is_category=True)))
    child = unwrap(library.add_tag(generate_tag("child", id=124)))

    panel: BuildTagPanel = BuildTagPanel(library, child)
    qtbot.addWidget(panel)

    assert __find_category_tag_widget(panel) is None

    child.parent_tags.add(parent)

    panel._add_parent_tag_callback(parent.id)
    tag_widget = __find_category_tag_widget(panel)
    assert tag_widget is not None
    assert tag_widget.tag == parent


def test_build_tag_panel_add_category_through_grandparent(
    qtbot: QtBot, library: Library, generate_tag: Callable[..., Tag]
):
    grandparent = unwrap(library.add_tag(generate_tag("grandparent", id=122, is_category=True)))
    parent = unwrap(library.add_tag(generate_tag("parent", id=123, parent_tags={grandparent})))
    child = unwrap(library.add_tag(generate_tag("child", id=124)))

    panel: BuildTagPanel = BuildTagPanel(library, child)
    qtbot.addWidget(panel)

    assert __find_category_tag_widget(panel) is None

    child.parent_tags.add(parent)

    panel._add_parent_tag_callback(parent.id)
    tag_widget = __find_category_tag_widget(panel)
    assert tag_widget is not None
    assert tag_widget.tag == grandparent


def test_build_tag_panel_remove_category_through_parent(
    qtbot: QtBot, library: Library, generate_tag: Callable[..., Tag]
):
    parent = unwrap(library.add_tag(generate_tag("parent", id=123, is_category=True)))
    child = unwrap(library.add_tag(generate_tag("child", id=124, parent_tags={parent})))

    panel: BuildTagPanel = BuildTagPanel(library, child)
    qtbot.addWidget(panel)

    tag_widget = __find_category_tag_widget(panel)
    assert tag_widget is not None
    assert tag_widget.tag == parent

    panel._remove_parent_tag_callback(parent.id)

    assert __find_category_tag_widget(panel) is None


def test_build_tag_panel_remove_category_through_grandparent(
    qtbot: QtBot, library: Library, generate_tag: Callable[..., Tag]
):
    grandparent = unwrap(library.add_tag(generate_tag("grandparent", id=122, is_category=True)))
    parent = unwrap(library.add_tag(generate_tag("parent", id=123, parent_tags={grandparent})))
    child = unwrap(library.add_tag(generate_tag("child", id=124, parent_tags={parent})))

    panel: BuildTagPanel = BuildTagPanel(library, child)
    qtbot.addWidget(panel)

    tag_widget = __find_category_tag_widget(panel)
    assert tag_widget is not None
    assert tag_widget.tag == grandparent

    panel._remove_parent_tag_callback(parent.id)

    assert __find_category_tag_widget(panel) is None


def test_build_tag_panel_exclude_from_category(
    qtbot: QtBot, library: Library, generate_tag: Callable[..., Tag]
):
    parent = unwrap(library.add_tag(generate_tag("parent", id=123, is_category=True)))
    child = unwrap(library.add_tag(generate_tag("child", id=124, parent_tags={parent})))

    panel: BuildTagPanel = BuildTagPanel(library, child)
    qtbot.addWidget(panel)

    assert len(panel.exclusion_ids) == 0

    tag_widget = __find_category_tag_widget(panel)
    assert tag_widget is not None

    checkbox = __find_include_checkbox(tag_widget)
    assert checkbox.isChecked()

    checkbox.click()

    assert parent.id in panel.exclusion_ids


def test_build_tag_panel_include_in_category(
    qtbot: QtBot, library: Library, generate_tag: Callable[..., Tag]
):
    parent = unwrap(library.add_tag(generate_tag("parent", id=123, is_category=True)))
    child = unwrap(
        library.add_tag(
            generate_tag("child", id=124, parent_tags={parent}, category_exclusions={parent})
        )
    )

    panel: BuildTagPanel = BuildTagPanel(library, child)
    qtbot.addWidget(panel)

    assert parent.id in panel.exclusion_ids

    tag_widget = __find_category_tag_widget(panel)
    assert tag_widget is not None

    checkbox = __find_include_checkbox(tag_widget)
    assert not checkbox.isChecked()

    checkbox.click()

    assert len(panel.exclusion_ids) == 0


def test_build_tag_panel_remove_duplicate_category_retained(
    qtbot: QtBot, library: Library, generate_tag: Callable[..., Tag]
):
    grandparent = unwrap(library.add_tag(generate_tag("grandparent", id=122, is_category=True)))
    parent = unwrap(library.add_tag(generate_tag("parent", id=123, parent_tags={grandparent})))
    other_parent = unwrap(
        library.add_tag(generate_tag("other_parent", id=124, parent_tags={grandparent}))
    )
    child = unwrap(
        library.add_tag(generate_tag("child", id=125, parent_tags={parent, other_parent}))
    )

    panel: BuildTagPanel = BuildTagPanel(library, child)
    qtbot.addWidget(panel)

    tag_widget = __find_category_tag_widget(panel)
    assert tag_widget is not None
    assert tag_widget.tag == grandparent

    panel._remove_parent_tag_callback(parent.id)

    tag_widget = __find_category_tag_widget(panel)
    assert tag_widget is not None
    assert tag_widget.tag == grandparent


def test_build_tag_panel_new_tag_multiple_categories(
    qtbot: QtBot, library: Library, generate_tag: Callable[..., Tag]
):
    parent = unwrap(library.add_tag(generate_tag("parent", id=123, is_category=True)))
    other_parent = unwrap(library.add_tag(generate_tag("other_parent", id=124, is_category=True)))

    panel: BuildTagPanel = BuildTagPanel(library)
    qtbot.addWidget(panel)

    tag_widget = __find_category_tag_widget(panel)
    assert tag_widget is None

    panel._add_parent_tag_callback(parent.id)

    tag_widget = __find_category_tag_widget(panel)
    assert tag_widget is not None
    assert tag_widget.tag == parent

    panel._add_parent_tag_callback(other_parent.id)

    tag_widget = __find_category_tag_widget(panel, 1)
    assert tag_widget is not None
    assert tag_widget.tag == other_parent


def test_build_tag_panel_category_not_shown_for_self(
    qtbot: QtBot, library: Library, generate_tag: Callable[..., Tag]
):
    library.add_tag(generate_tag("category", id=123, is_category=True))

    panel: BuildTagPanel = BuildTagPanel(library)
    qtbot.addWidget(panel)

    tag_widget = __find_category_tag_widget(panel)
    assert tag_widget is None


def test_build_tag_panel_remove_inherited_from_multiple_parents_during_tag_creation(
    qtbot: QtBot, library: Library, generate_tag: Callable[..., Tag]
):
    parent = unwrap(library.add_tag(generate_tag("parent", id=123, is_category=True)))
    child1 = unwrap(library.add_tag(generate_tag("child1", id=124, parent_tags={parent})))
    child2 = unwrap(library.add_tag(generate_tag("child2", id=125, parent_tags={parent})))

    panel: BuildTagPanel = BuildTagPanel(library)
    qtbot.addWidget(panel)

    panel._add_parent_tag_callback(124)
    panel._add_parent_tag_callback(125)

    tag_widget = __find_category_tag_widget(panel)
    assert tag_widget is not None

    panel._remove_parent_tag_callback(child1.id)
    tag_widget = __find_category_tag_widget(panel)
    assert tag_widget is not None

    panel._remove_parent_tag_callback(child2.id)
    tag_widget = __find_category_tag_widget(panel)
    assert tag_widget is None


def test_build_tag_panel_add_different_category_after_removing_other_category(
    qtbot: QtBot, library: Library, generate_tag: Callable[..., Tag]
):
    category = unwrap(library.add_tag(generate_tag("category", id=123, is_category=True)))
    tag = unwrap(library.add_tag(generate_tag("tag", id=124, parent_tags={category})))
    other = unwrap(library.add_tag(generate_tag("other", id=125)))

    panel: BuildTagPanel = BuildTagPanel(library, tag)
    qtbot.addWidget(panel)

    tag_widget = __find_category_tag_widget(panel)
    assert tag_widget is not None

    panel._remove_parent_tag_callback(category.id)
    tag_widget = __find_category_tag_widget(panel)
    assert tag_widget is None

    panel._add_parent_tag_callback(other.id)
    tag_widget = __find_category_tag_widget(panel)
    assert tag_widget is None


def test_build_tag_panel_remove_category_inherited_directly_and_indirectly(
    qtbot: QtBot, library: Library, generate_tag: Callable[..., Tag]
):
    parent = unwrap(library.add_tag(generate_tag("parent", id=123, is_category=True)))
    child = unwrap(library.add_tag(generate_tag("child", id=124, parent_tags={parent})))
    grandchild = unwrap(
        library.add_tag(generate_tag("grandchild", id=125, parent_tags={parent, child}))
    )

    panel: BuildTagPanel = BuildTagPanel(library, grandchild)
    qtbot.addWidget(panel)

    tag_widget = __find_category_tag_widget(panel)
    assert tag_widget is not None

    panel._remove_parent_tag_callback(parent.id)
    tag_widget = __find_category_tag_widget(panel)
    assert tag_widget is not None

    panel._remove_parent_tag_callback(child.id)
    tag_widget = __find_category_tag_widget(panel)
    assert tag_widget is None


def __find_category_tag_widget(panel: BuildTagPanel, index: int = 0) -> TagWidget | None:
    item = panel.category_scroll_layout.itemAt(0).widget().layout().itemAt(index)
    while item is not None:
        if isinstance(item.widget(), TagWidget):
            break
        item = item.widget().layout().itemAt(0)

    if item is not None:
        return cast(TagWidget, item.widget())
    return None


def __find_include_checkbox(tag_widget: TagWidget) -> QCheckBox:
    layout_item = tag_widget.parentWidget().layout().itemAt(1)
    assert layout_item is not None

    widget = layout_item.widget()
    assert isinstance(widget, QCheckBox)

    return widget
