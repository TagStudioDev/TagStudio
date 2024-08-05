from src.core.library import Entry
from src.qt.widgets.tag import TagWidget
from src.qt.widgets.tag_box import TagBoxWidget


def test_tag_widget(qtbot, library, qt_driver):
    entry = library.entries[0]

    tag_widget = TagBoxWidget(entry, "title", [], qt_driver)

    qtbot.add_widget(tag_widget)

    tag_widget.add_button.clicked.emit()


def test_tag_widget_chosen(qtbot, library, qt_driver):
    entry = library.entries[0]

    tag_widget = TagBoxWidget(entry, "title", [], qt_driver)

    qtbot.add_widget(tag_widget)

    tag_widget.driver.selected = [0]
    tag_widget.add_modal.widget.tag_chosen.emit(1)


def test_tag_widget_remove(qtbot, qt_driver):
    entry: Entry = qt_driver.lib.entries[0]

    tag = list(entry.tags)[0]
    assert tag

    assert entry.tag_box_fields
    assert entry.tag_box_fields[0].tags

    tag_widget = TagBoxWidget(entry, "title", [tag], qt_driver)
    tag_widget.driver.selected = [0]

    qtbot.add_widget(tag_widget)

    # get all widgets from `tag_widget.base_layout`
    tag_widget = tag_widget.base_layout.itemAt(0).widget()
    assert isinstance(tag_widget, TagWidget)

    tag_widget.remove_button.clicked.emit()

    entry: Entry = qt_driver.lib.entries[0]
    assert not entry.tag_box_fields[0].tags
