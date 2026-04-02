# Copyright (C) 2025
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio


from collections.abc import Callable

from PySide6.QtWidgets import QCheckBox
from pytestqt.qtbot import QtBot

from tagstudio.core.library.alchemy.library import Library
from tagstudio.core.library.alchemy.models import Tag, TagAlias
from tagstudio.core.utils.types import unwrap
from tagstudio.qt.mixed.build_tag import BuildTagPanel, CustomTableItem
from tagstudio.qt.mixed.tag_widget import TagWidget
from tagstudio.qt.translations import Translations


def test_build_tag_panel_add_sub_tag_callback(
    qtbot: QtBot, library: Library, generate_tag: Callable[..., Tag]
):
    parent = unwrap(library.add_tag(generate_tag("xxx", id=123)))
    child = unwrap(library.add_tag(generate_tag("xx", id=124)))

    panel: BuildTagPanel = BuildTagPanel(library, child)
    qtbot.addWidget(panel)

    panel.add_parent_tag_callback(parent.id)

    assert len(panel.parent_ids) == 1


def test_build_tag_panel_remove_subtag_callback(
    qtbot: QtBot, library: Library, generate_tag: Callable[..., Tag]
):
    parent = unwrap(library.add_tag(generate_tag("xxx", id=123)))
    child = unwrap(library.add_tag(generate_tag("xx", id=124)))

    library.update_tag(child, {parent.id}, [], [])

    child = unwrap(library.get_tag(child.id))

    panel: BuildTagPanel = BuildTagPanel(library, child)
    qtbot.addWidget(panel)

    panel.remove_parent_tag_callback(parent.id)

    assert len(panel.parent_ids) == 0


import os

os.environ["QT_QPA_PLATFORM"] = "offscreen"


def test_build_tag_panel_add_alias_callback(
    qtbot: QtBot, library: Library, generate_tag: Callable[..., Tag]
):
    tag = unwrap(library.add_tag(generate_tag("xxx", id=123)))

    panel: BuildTagPanel = BuildTagPanel(library, tag)
    qtbot.addWidget(panel)

    panel.add_alias_callback()

    assert panel.aliases_table.rowCount() == 1


def test_build_tag_panel_remove_alias_callback(
    qtbot: QtBot, library: Library, generate_tag: Callable[..., Tag]
):
    tag: Tag = unwrap(library.add_tag(generate_tag("xxx", id=123)))

    library.update_tag(tag, [], {"alias", "alias_2"}, {123, 124})

    tag = unwrap(library.get_tag(tag.id))

    assert "alias" in tag.alias_strings
    assert "alias_2" in tag.alias_strings

    panel: BuildTagPanel = BuildTagPanel(library, tag)
    qtbot.addWidget(panel)

    alias: TagAlias = unwrap(library.get_alias(tag.id, tag.alias_ids[0]))

    panel.remove_alias_callback(alias.name, alias.id)

    assert len(panel.alias_ids) == 1
    assert len(panel.alias_names) == 1
    assert alias.name not in panel.alias_names


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

    library.update_tag(tag, [], {"alias", "alias_2"}, {123, 124})

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

    old_text = widget.text()
    widget.setText("alias_update")

    panel.add_aliases()

    assert old_text not in panel.alias_names
    assert "alias_update" in panel.alias_names
    assert len(panel.alias_names) == 2


def test_build_tag_panel_set_aliases(
    qtbot: QtBot, library: Library, generate_tag: Callable[..., Tag]
):
    tag: Tag = unwrap(library.add_tag(generate_tag("xxx", id=123)))

    library.update_tag(tag, [], {"alias"}, {123})

    tag = unwrap(library.get_tag(tag.id))

    assert len(tag.alias_ids) == 1

    panel: BuildTagPanel = BuildTagPanel(library, tag)
    qtbot.addWidget(panel)

    assert panel.aliases_table.rowCount() == 1
    assert len(panel.alias_names) == 1
    assert len(panel.alias_ids) == 1


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

    panel.add_parent_tag_callback(parent.id)
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

    panel.add_parent_tag_callback(parent.id)
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

    panel.remove_parent_tag_callback(parent.id)

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

    panel.remove_parent_tag_callback(parent.id)

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

    panel.remove_parent_tag_callback(parent.id)

    tag_widget = __find_category_tag_widget(panel)
    assert tag_widget is not None
    assert tag_widget.tag == grandparent


def __find_category_tag_widget(panel: BuildTagPanel) -> TagWidget | None:
    item = panel.category_scroll_layout.itemAt(0)
    while item is not None:
        if isinstance(item.widget(), TagWidget):
            break
        item = item.widget().layout().itemAt(0)

    if item is not None:
        return item.widget()
    return None


def __find_include_checkbox(tag_widget: TagWidget) -> QCheckBox:
    layout_item = tag_widget.parentWidget().layout().itemAt(1)
    assert layout_item is not None

    widget = layout_item.widget()
    assert isinstance(widget, QCheckBox)

    return widget
