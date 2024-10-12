from typing import cast

from PySide6.QtWidgets import QApplication, QMainWindow
from src.core.library.alchemy.models import Tag
from src.qt.modals.build_tag import BuildTagPanel
from src.qt.widgets.tag import TagAliasWidget


def test_build_tag_panel_add_sub_tag_callback(library, generate_tag):
    parent = library.add_tag(generate_tag("xxx", id=123))
    child = library.add_tag(generate_tag("xx", id=124))
    assert child
    assert parent

    panel: BuildTagPanel = BuildTagPanel(library, child)

    panel.add_subtag_callback(parent.id)

    assert len(panel.subtag_ids) == 1


def test_build_tag_panel_remove_subtag_callback(library, generate_tag):
    parent = library.add_tag(generate_tag("xxx", id=123))
    child = library.add_tag(generate_tag("xx", id=124))
    assert child
    assert parent

    library.update_tag(child, {parent.id}, [], [])

    child = library.get_tag(child.id)

    assert child

    panel: BuildTagPanel = BuildTagPanel(library, child)

    panel.remove_subtag_callback(parent.id)

    assert len(panel.subtag_ids) == 0


import os

os.environ["QT_QPA_PLATFORM"] = "offscreen"


def test_build_tag_panel_remove_selected_alias(library, generate_tag):
    app = QApplication.instance() or QApplication([])

    window = QMainWindow()
    parent_tag = library.add_tag(generate_tag("xxx", id=123))
    panel = BuildTagPanel(library, parent_tag)
    panel.setParent(window)

    panel.add_alias_callback()
    window.show()

    assert panel.aliases_flow_layout.count() == 2

    alias_widget = panel.aliases_flow_layout.itemAt(0).widget()
    alias_widget.text_field.setFocus()

    app.processEvents()

    panel.remove_selected_alias()

    assert panel.aliases_flow_layout.count() == 1


def test_build_tag_panel_add_alias_callback(library, generate_tag):
    tag = library.add_tag(generate_tag("xxx", id=123))
    assert tag

    panel: BuildTagPanel = BuildTagPanel(library, tag)

    panel.add_alias_callback()

    assert panel.aliases_flow_layout.count() == 2


def test_build_tag_panel_remove_alias_callback(library, generate_tag):
    tag = library.add_tag(generate_tag("xxx", id=123))
    assert tag

    library.update_tag(tag, [], {"alias", "alias_2"}, {123, 124})

    tag = library.get_tag(tag.id)

    assert "alias" in tag.alias_strings
    assert "alias_2" in tag.alias_strings

    panel: BuildTagPanel = BuildTagPanel(library, tag)

    alias = library.get_alias(tag.id, tag.alias_ids[0])

    panel.remove_alias_callback(alias.name, alias.id)

    assert len(panel.alias_ids) == 1
    assert len(panel.alias_names) == 1
    assert alias.name not in panel.alias_names


def test_build_tag_panel_set_subtags(library, generate_tag):
    parent = library.add_tag(generate_tag("parent", id=123))
    child = library.add_tag(generate_tag("child", id=124))
    assert parent
    assert child

    library.add_subtag(child.id, parent.id)

    child = library.get_tag(child.id)

    panel: BuildTagPanel = BuildTagPanel(library, child)

    assert len(panel.subtag_ids) == 1
    assert panel.subtag_flow_layout.count() == 2


def test_build_tag_panel_add_aliases(library, generate_tag):
    tag = library.add_tag(generate_tag("xxx", id=123))
    assert tag

    library.update_tag(tag, [], {"alias", "alias_2"}, {123, 124})

    tag = library.get_tag(tag.id)

    assert "alias" in tag.alias_strings
    assert "alias_2" in tag.alias_strings

    panel: BuildTagPanel = BuildTagPanel(library, tag)

    widget = panel.aliases_flow_layout.itemAt(0).widget()

    alias_names: set[str] = set()
    alias_names.add(cast(TagAliasWidget, widget).text_field.text())

    widget = panel.aliases_flow_layout.itemAt(1).widget()
    alias_names.add(cast(TagAliasWidget, widget).text_field.text())

    assert "alias" in alias_names
    assert "alias_2" in alias_names

    old_text = cast(TagAliasWidget, widget).text_field.text()
    cast(TagAliasWidget, widget).text_field.setText("alias_update")

    panel.add_aliases()

    assert old_text not in panel.alias_names
    assert "alias_update" in panel.alias_names
    assert len(panel.alias_names) == 2


def test_build_tag_panel_set_aliases(library, generate_tag):
    tag = library.add_tag(generate_tag("xxx", id=123))
    assert tag

    library.update_tag(tag, [], {"alias"}, {123})

    tag = library.get_tag(tag.id)

    assert len(tag.alias_ids) == 1

    panel: BuildTagPanel = BuildTagPanel(library, tag)

    assert panel.aliases_flow_layout.count() == 2
    assert len(panel.alias_names) == 1
    assert len(panel.alias_ids) == 1


def test_build_tag_panel_set_tag(library, generate_tag):
    tag = library.add_tag(generate_tag("xxx", id=123))
    assert tag

    panel: BuildTagPanel = BuildTagPanel(library, tag)

    assert panel.tag
    assert panel.tag.name == "xxx"


def test_build_tag_panel_build_tag(library):
    panel: BuildTagPanel = BuildTagPanel(library)

    tag: Tag = panel.build_tag()

    assert tag
    assert tag.name == "New Tag"
