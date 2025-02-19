from src.core.library import Tag
from src.qt.modals.build_tag import BuildTagPanel


def test_tag_panel(qtbot, library):
    panel = BuildTagPanel(library)

    qtbot.addWidget(panel)


def test_add_tag_callback(qt_driver):
    # Given
    assert len(qt_driver.lib.tags) == 6
    qt_driver.add_tag_action_callback()

    # When
    qt_driver.modal.widget.name_field.setText("xxx")
    # qt_driver.modal.widget.color_field.setCurrentIndex(1)
    qt_driver.modal.saved.emit()

    # Then
    tags: set[Tag] = qt_driver.lib.tags
    assert len(tags) == 7
    assert "xxx" in {tag.name for tag in tags}
