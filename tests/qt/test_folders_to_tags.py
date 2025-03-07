from src.qt.modals.folders_to_tags import generate_preview_data


def test_generate_preview_data(library, snapshot):
    preview = generate_preview_data(library)

    assert preview == snapshot
