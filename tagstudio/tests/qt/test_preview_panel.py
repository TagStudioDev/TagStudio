from src.core.library.alchemy.enums import FieldTypeEnum
from src.core.library.alchemy.fields import _FieldID, TextField
from src.qt.widgets.preview_panel import PreviewPanel
from tests.test_library import generate_entry


def test_update_widgets_not_selected(qt_driver, library):
    qt_driver.frame_content = list(library._entries)
    qt_driver.selected = []

    panel = PreviewPanel(library, qt_driver)
    panel.update_widgets()

    assert panel.preview_img.isVisible()
    assert panel.file_label.text() == "No Items Selected"


def test_update_widgets_single_selected(qt_driver, library):
    qt_driver.frame_content = list(library._entries)
    qt_driver.selected = [0]

    panel = PreviewPanel(library, qt_driver)
    panel.update_widgets()

    assert panel.preview_img.isVisible()


def test_update_widgets_multiple_selected(qt_driver, library):
    # entry with no tag fields
    entry = generate_entry(fields=[TextField(type_key=_FieldID.TITLE.name)])

    assert not entry.tag_box_fields

    library.add_entries([entry])
    assert library.entries_count == 3

    qt_driver.frame_content = list(library._entries)
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


def test_write_container_text_line(qt_driver, library):
    # Given
    panel = PreviewPanel(library, qt_driver)
    entry = next(library._entries_full)

    field = entry.text_fields[0]
    assert len(entry.text_fields) == 1
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
    entry = next(library._entries_full)
    # the value was updated
    assert entry.text_fields[0].value == "bar"


def test_remove_field(qt_driver, library):
    # Given
    panel = PreviewPanel(library, qt_driver)
    entries = list(library._entries_full)
    qt_driver.frame_content = entries
    panel.selected = [1]

    field = entries[1].text_fields[0]
    panel.write_container(0, field)
    panel.remove_field(field)

    entries = list(library._entries_full)
    assert not entries[1].text_fields


def test_update_field(qt_driver, library):
    panel = PreviewPanel(library, qt_driver)

    qt_driver.frame_content = list(library._entries)[:2]
    qt_driver.selected = [0, 1]
    panel.selected = [0, 1]

    field = [
        x
        for x in next(library._entries_full).text_fields
        if x.type.type == FieldTypeEnum.TEXT_LINE
    ][0]

    panel.update_field(field, "meow")

    for entry in list(library._entries_full)[:2]:
        field = [
            x for x in entry.text_fields if x.type.type == FieldTypeEnum.TEXT_LINE
        ][0]
        assert field.value == "meow"
