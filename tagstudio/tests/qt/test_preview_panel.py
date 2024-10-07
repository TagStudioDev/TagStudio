from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
from src.core.library import Entry
from src.core.library.alchemy.enums import FieldTypeEnum
from src.core.library.alchemy.fields import TextField, _FieldID
from src.qt.widgets.preview_panel import PreviewPanel


def test_update_widgets_not_selected(qt_driver, library):
    qt_driver.frame_content = list(library.get_entries())
    qt_driver.selected = []

    panel = PreviewPanel(library, qt_driver)
    panel.update_widgets()

    assert panel.preview_img.isVisible()
    assert panel.file_label.text() == "<i>No Items Selected</i>"


@pytest.mark.parametrize("library", [TemporaryDirectory()], indirect=True)
def test_update_widgets_single_selected(qt_driver, library):
    qt_driver.frame_content = list(library.get_entries())
    qt_driver.selected = [0]

    panel = PreviewPanel(library, qt_driver)
    panel.update_widgets()

    assert panel.preview_img.isVisible()


def test_update_widgets_multiple_selected(qt_driver, library):
    # entry with no tag fields
    entry = Entry(
        path=Path("test.txt"),
        folder=library.folder,
        fields=[TextField(type_key=_FieldID.TITLE.name, position=0)],
    )

    assert not entry.tag_box_fields

    library.add_entries([entry])
    assert library.entries_count == 3

    qt_driver.frame_content = list(library.get_entries())
    qt_driver.selected = [0, 1, 2]

    panel = PreviewPanel(library, qt_driver)
    panel.update_widgets()

    assert {f.type_key for f in panel.common_fields} == {
        _FieldID.TITLE.name,
    }

    assert {f.type_key for f in panel.mixed_fields} == {
        _FieldID.TAGS.name,
        _FieldID.TAGS_META.name,
    }


def test_write_container_text_line(qt_driver, entry_full, library):
    # Given
    panel = PreviewPanel(library, qt_driver)

    field = entry_full.text_fields[0]
    assert len(entry_full.text_fields) == 1
    assert field.type.type == FieldTypeEnum.TEXT_LINE
    assert field.type.name == "Title"

    # set any value
    field.value = "foo"
    panel.write_container(0, field)
    panel.selected = [0]

    assert len(panel.containers) == 1
    container = panel.containers[0]
    widget = container.get_inner_widget()
    # test it's not "mixed data"
    assert widget.text_label.text() == "foo"

    # When update and submit modal
    modal = panel.containers[0].modal
    modal.widget.text_edit.setText("bar")
    modal.save_button.click()

    # Then reload entry
    entry_full = next(library.get_entries(with_joins=True))
    # the value was updated
    assert entry_full.text_fields[0].value == "bar"


def test_remove_field(qt_driver, library):
    # Given
    panel = PreviewPanel(library, qt_driver)
    entries = list(library.get_entries(with_joins=True))
    qt_driver.frame_content = entries

    # When second entry is selected
    panel.selected = [1]

    field = entries[1].text_fields[0]
    panel.write_container(0, field)
    panel.remove_field(field)

    entries = list(library.get_entries(with_joins=True))
    assert not entries[1].text_fields


def test_update_field(qt_driver, library, entry_full):
    panel = PreviewPanel(library, qt_driver)

    # select both entries
    qt_driver.frame_content = list(library.get_entries())[:2]
    qt_driver.selected = [0, 1]
    panel.selected = [0, 1]

    # update field
    title_field = entry_full.text_fields[0]
    panel.update_field(title_field, "meow")

    for entry in library.get_entries(with_joins=True):
        field = [x for x in entry.text_fields if x.type_key == title_field.type_key][0]
        assert field.value == "meow"
