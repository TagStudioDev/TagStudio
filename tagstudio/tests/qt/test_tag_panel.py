from src.qt.modals.build_tag import BuildTagPanel


def test_tag_panel(qtbot, library):
    panel = BuildTagPanel(library)

    qtbot.addWidget(panel)


def test_add_tag_callback(qt_driver):
    # Given
    assert len(qt_driver.lib.tags) == 1
    qt_driver.add_tag_action_callback()

    # When
    qt_driver.modal.widget.name_field.setText("bar")
    qt_driver.modal.widget.color_field.setCurrentIndex(1)
    qt_driver.modal.saved.emit()

    # Then
    tags = qt_driver.lib.tags
    assert len(tags) == 2
    assert tags[1].name == "bar"
