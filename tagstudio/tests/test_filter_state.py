import pytest
from src.core.library.alchemy.enums import FilterState


def test_filter_state_query():
    # Given
    query = "tag:foo"
    state = FilterState(query=query)

    # When
    assert state.tag == "foo"


@pytest.mark.parametrize(
    ["attribute", "comparator"],
    [
        ("tag", str),
        ("tag_id", int),
        ("path", str),
        ("name", str),
        ("id", int),
    ],
)
def test_filter_state_attrs_compare(attribute, comparator):
    # When
    state = FilterState(**{attribute: "2"})

    # Then
    # compare the attribute value
    assert getattr(state, attribute) == comparator("2")

    # Then
    for prop in ("tag", "tag_id", "path", "name", "id"):
        if prop == attribute:
            continue
        assert not getattr(state, prop)
