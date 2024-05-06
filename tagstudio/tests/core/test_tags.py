from src.core.library import Tag


def test_construction():
    tag = Tag(
        id=1,
        name="Tag Name",
        shorthand="TN",
        aliases=["First A", "Second A"],
        subtags_ids=[2, 3, 4],
        color="",
    )
    assert tag

def test_empty_construction():
    tag = Tag(id=1, name="", shorthand="", aliases=[], subtags_ids=[], color="")
    assert tag
