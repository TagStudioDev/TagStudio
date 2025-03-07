from src.qt.modals.folders_to_tags import folders_to_tags


def test_folders_to_tags(library):
    folders_to_tags(library)
    entry = [x for x in library.get_entries(with_joins=True) if "bar.md" in str(x.path)][0]
    assert {x.name for x in entry.tags} == {"two", "bar"}
