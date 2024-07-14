from src.qt.modals.tag_search import TagSearchPanel


def test_update_tags(qtbot, library):
    # Given
    panel = TagSearchPanel(library)

    qtbot.addWidget(panel)

    # When
    panel.update_tags()
