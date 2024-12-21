from unittest.mock import patch

from src.core.library.alchemy.fields import _FieldID
from src.qt.modals.build_tag import BuildTagPanel
from src.qt.widgets.tag import TagWidget
from src.qt.widgets.tag_box import TagBoxWidget


def test_tag_widget(qtbot, library, qt_driver):
    # given
    entry = next(library.get_entries(with_joins=True))
    field = entry.tag_box_fields[0]

    tag_widget = TagBoxWidget(field, "title", qt_driver)

    qtbot.add_widget(tag_widget)

    assert not tag_widget.add_modal.isVisible()

    # when/then check no exception is raised
    tag_widget.add_button.clicked.emit()
    # check `tag_widget.add_modal` is visible
    assert tag_widget.add_modal.isVisible()


def test_tag_widget_add_existing_raises(library, qt_driver, entry_full):
    # Given
    tag_field = [f for f in entry_full.tag_box_fields if f.type_key == _FieldID.TAGS.name][0]
    assert len(entry_full.tags) == 1
    tag = next(iter(entry_full.tags))

    # When
    tag_widget = TagBoxWidget(tag_field, "title", qt_driver)
    tag_widget.driver.frame_content = [entry_full]
    tag_widget.driver.selected = [0]

    # Then
    with patch.object(tag_widget, "error_occurred") as mocked:
        tag_widget.add_modal.widget.tag_chosen.emit(tag.id)
        assert mocked.emit.called


def test_tag_widget_add_new_pass(qtbot, library, qt_driver, generate_tag):
    # Given
    entry = next(library.get_entries(with_joins=True))
    field = entry.tag_box_fields[0]

    tag = generate_tag(name="new_tag")
    library.add_tag(tag)

    tag_widget = TagBoxWidget(field, "title", qt_driver)

    qtbot.add_widget(tag_widget)

    tag_widget.driver.selected = [0]
    with patch.object(tag_widget, "error_occurred") as mocked:
        # When
        tag_widget.add_modal.widget.tag_chosen.emit(tag.id)

        # Then
        assert not mocked.emit.called


def test_tag_widget_remove(qtbot, qt_driver, library, entry_full):
    tag = list(entry_full.tags)[0]
    assert tag

    assert entry_full.tag_box_fields
    tag_field = [f for f in entry_full.tag_box_fields if f.type_key == _FieldID.TAGS.name][0]

    tag_widget = TagBoxWidget(tag_field, "title", qt_driver)
    tag_widget.driver.selected = [0]

    qtbot.add_widget(tag_widget)

    tag_widget = tag_widget.base_layout.itemAt(0).widget()
    assert isinstance(tag_widget, TagWidget)

    tag_widget.remove_button.clicked.emit()

    entry = next(qt_driver.lib.get_entries(with_joins=True))
    assert not entry.tag_box_fields[0].tags


def test_tag_widget_edit(qtbot, qt_driver, library, entry_full):
    # Given
    entry = next(library.get_entries(with_joins=True))
    library.add_tag(list(entry.tags)[0])
    tag = library.get_tag(list(entry.tags)[0].id)
    assert tag

    assert entry_full.tag_box_fields
    tag_field = [f for f in entry_full.tag_box_fields if f.type_key == _FieldID.TAGS.name][0]

    tag_box_widget = TagBoxWidget(tag_field, "title", qt_driver)
    tag_box_widget.driver.selected = [0]

    qtbot.add_widget(tag_box_widget)

    tag_widget = tag_box_widget.base_layout.itemAt(0).widget()
    assert isinstance(tag_widget, TagWidget)

    # When
    tag_box_widget.edit_tag(tag)

    # Then
    panel = tag_box_widget.edit_modal.widget
    assert isinstance(panel, BuildTagPanel)
    assert panel.tag.name == tag.name
    assert panel.name_field.text() == tag.name
