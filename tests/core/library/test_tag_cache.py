# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: MIT


from pytest import MonkeyPatch

from tagstudio.core.constants import TAG_ARCHIVED
from tagstudio.core.library.alchemy.library import Library
from tagstudio.core.library.alchemy.models import Tag, TagAlias
from tagstudio.core.library.tag_cache import CachedTag, TagCache
from tagstudio.core.utils.types import unwrap


def found_tags(library: Library, query: str) -> list[CachedTag]:
    return [unwrap(library.get_cached_tag(tag_id)) for tag_id in library.search_tags(query)]


def found_names(library: Library, query: str) -> list[str]:
    return [tag.name for tag in found_tags(library, query)]


def cached_tags(name: str) -> dict[int, CachedTag]:
    tag = CachedTag(
        id=1,
        name=name,
        shorthand=None,
        aliases=(),
        color=None,
        disambiguation_id=None,
        is_category=False,
        parent_ids=(),
        exclusion_ids=(),
    )
    return {1: tag}


def test_tag_search_lists_names_starting_with_the_query_first_shortest_first(library: Library):
    assert library.add_tag(Tag(name="Bobcat"))
    assert library.add_tag(Tag(name="Cattle"))
    assert library.add_tag(Tag(name="Cat"))

    assert found_names(library, "cat") == ["Cat", "Cattle", "Bobcat"]


def test_tag_search_lists_descendants_after_matches(library: Library):
    animals = library.add_tag(Tag(name="Animals"))
    assert animals
    assert library.add_tag(Tag(name="Aardvark"), parent_ids={animals.id})

    assert found_names(library, "nimal") == ["Animals", "Aardvark"]


def test_tag_search_casefolds_sharp_s(library: Library):
    assert library.add_tag(Tag(name="Straße"))

    assert found_names(library, "strasse") == ["Straße"]


def test_tag_search_matches_shorthands(library: Library):
    assert library.add_tag(Tag(name="Long Name", shorthand="LN"))

    assert found_names(library, "LN") == ["Long Name"]


def test_tag_display_shows_disambiguation_names(library: Library):
    assert library.add_tag(Tag(name="baz", disambiguation_id=1500), parent_ids={1500})

    assert [library.tag_display_name(tag) for tag in found_tags(library, "baz")] == ["baz (subbar)"]


def test_tag_display_shows_disambiguation_tag_with_id_0(library: Library):
    """Catches an edge case where the Archived tag (ID 0) isn't shown for disambiguation."""
    assert library.add_tag(
        Tag(name="baz", disambiguation_id=TAG_ARCHIVED), parent_ids={TAG_ARCHIVED}
    )

    assert [library.tag_display_name(tag) for tag in found_tags(library, "baz")] == [
        "baz (Archived)"
    ]


def test_tag_search_matches_display_names(library: Library):
    assert library.add_tag(Tag(name="baz", disambiguation_id=1500), parent_ids={1500})

    assert found_names(library, "baz (sub") == ["baz"]


def test_tag_search_lists_display_names_starting_with_the_query_first(library: Library):
    assert library.add_tag(Tag(name="Abaz", disambiguation_id=1500), parent_ids={1500})
    assert library.add_tag(Tag(name="baz", disambiguation_id=1500), parent_ids={1500})

    assert found_names(library, "baz (sub") == ["baz", "Abaz"]


def test_tag_ids_by_name_match_whole_names_only(library: Library):
    assert library.get_tag_ids_by_name("BAR") == {2000}


def test_tag_ids_by_name_match_underscores_as_spaces(library: Library):
    tag = library.add_tag(Tag(name="Tag Name With Spaces"))
    assert tag

    assert library.get_tag_ids_by_name("Tag_Name_With_Spaces") == {tag.id}


def test_tag_ids_by_name_match_names_mixing_spaces_and_underscores(library: Library):
    tag = library.add_tag(Tag(name="foo_bar baz"))
    assert tag

    assert library.get_tag_ids_by_name("foo_bar_baz") == {tag.id}


def test_tag_search_matches_aliases(library: Library):
    assert library.add_tag(Tag(name="Cat"), aliases={TagAlias(name="Kitty")})

    assert found_names(library, "kitty") == ["Cat"]


def test_removed_tag_is_not_found(library: Library):
    assert library.remove_tag(2000)

    assert found_names(library, "bar") == ["subbar"]


def test_removed_parent_tag_leaves_no_descendants(library: Library):
    assert library.remove_tag(1500)

    assert library.get_tag_ids_with_descendants({1500}) == {1500}


def test_removed_disambiguation_tag_leaves_plain_display_names(library: Library):
    assert library.add_tag(Tag(name="baz", disambiguation_id=1500), parent_ids={1500})
    assert library.remove_tag(1500)

    assert [library.tag_display_name(tag) for tag in found_tags(library, "baz")] == ["baz"]


def test_tag_cache_reads_refreshed_tags_during_load(
    monkeypatch: MonkeyPatch,
):
    reads: list[str] = []

    def read_cached_tags(tag_ids: set[int] | None) -> dict[int, CachedTag]:
        if tag_ids is None and not reads:
            reads.append("stale")
            cache.refresh_tags({1})
            return cached_tags("stale")
        reads.append("fresh")
        return cached_tags("fresh")

    cache = TagCache(None)
    monkeypatch.setattr(cache, "_read_cached_tags", read_cached_tags)

    assert cache.load().tags[1].name == "fresh"
    assert reads == ["stale", "fresh"]


def test_tag_cache_reloads_after_a_failed_refresh(monkeypatch: MonkeyPatch):
    names = ["first", "second"]

    def read_cached_tags(tag_ids: set[int] | None) -> dict[int, CachedTag]:
        if tag_ids is not None:
            raise OSError
        return cached_tags(names.pop(0))

    cache = TagCache(None)
    monkeypatch.setattr(cache, "_read_cached_tags", read_cached_tags)
    cache.load()
    cache.refresh_tags({1})

    assert cache.load().tags[1].name == "second"
