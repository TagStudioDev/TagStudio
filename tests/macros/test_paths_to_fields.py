# Copyright (C) 2025
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio

from pathlib import Path

from tagstudio.core.library.alchemy.fields import FieldID
from tagstudio.core.library.alchemy.library import Library
from tagstudio.core.library.alchemy.models import Entry
from tagstudio.core.utils.types import unwrap
from tagstudio.qt.mixed.paths_to_fields import (
    PathFieldRule,
    apply_paths_to_fields,
    iter_preview_paths_to_fields,
    preview_paths_to_fields,
)


def test_paths_to_fields_preview_and_apply(library: Library):
    folder = unwrap(library.folder)

    entries = [
        Entry(folder=folder, path=Path("series-MySeries/01_10.jpg"), fields=[]),
        Entry(folder=folder, path=Path("creator-jdoe/abc123_02.png"), fields=[]),
        Entry(
            folder=folder,
            path=Path("creator-jane/Some-Series_source-name_003.jpeg"),
            fields=[],
        ),
    ]
    ids = library.add_entries(entries)

    rules = [
        # series-{series}/{page}_{total}.ext
        PathFieldRule(
            pattern=r"^series-(?P<series>[^/]+)/(?P<page>\d+)_\d+\.[^.]+$",
            fields={
                FieldID.SERIES.name: "$series",
                "page_number": "$page",
            },
        ),
        # creator-{artist}/{source_ident}_{page}.ext -> artist + source URL
        PathFieldRule(
            pattern=r"^creator-(?P<artist>[^/]+)/(?P<source_ident>[^_]+)_(?P<page>\d+)\.[^.]+$",
            fields={
                FieldID.ARTIST.name: "$artist",
                FieldID.SOURCE.name: "example.com/abc/$source_ident",
            },
        ),
        # creator-{artist}/{series}_{source}_{page}.ext
        PathFieldRule(
            pattern=r"^creator-(?P<artist>[^/]+)/(?P<series>[^_]+)_(?P<source>[^_]+)_(?P<page>\d+)\.[^.]+$",
            fields={
                FieldID.ARTIST.name: "$artist",
                FieldID.SERIES.name: "$series",
                FieldID.SOURCE.name: "$source",
                "page_number": "$page",
            },
        ),
    ]

    preview = preview_paths_to_fields(library, rules)
    # should propose updates for all 3 entries
    assert len(preview) == 3

    applied = apply_paths_to_fields(library, preview, create_missing_field_types=True)
    # ** TODO: The test only verifies that 'applied >= 5' but doesn't 
    #   verify the exact number or check for potential duplicate field assignments.
    assert applied >= 5  # at least series + page + artist + source for 2 rules

    # Validate the fields were set as expected
    e0 = unwrap(library.get_entry_full(ids[0]))
    kv0 = {f.type_key: (f.value or "") for f in e0.fields}
    assert kv0.get(FieldID.SERIES.name) == "MySeries"
    assert kv0.get("page_number") == "01"

    e1 = unwrap(library.get_entry_full(ids[1]))
    kv1 = {f.type_key: (f.value or "") for f in e1.fields}
    assert kv1.get(FieldID.ARTIST.name) == "jdoe"
    assert kv1.get(FieldID.SOURCE.name) == "example.com/abc/abc123"

    e2 = unwrap(library.get_entry_full(ids[2]))
    kv2 = {f.type_key: (f.value or "") for f in e2.fields}
    assert kv2.get(FieldID.ARTIST.name) == "jane"
    assert kv2.get(FieldID.SERIES.name) == "Some-Series"
    assert kv2.get(FieldID.SOURCE.name) == "source-name"
    assert kv2.get("page_number") == "003"


def test_paths_to_fields_allows_duplicate_fields(library: Library):
    folder = unwrap(library.folder)

    entry = Entry(folder=folder, path=Path("multi-foo_bar.jpg"), fields=[])
    [eid] = library.add_entries([entry])

    rule = PathFieldRule(
        pattern=r"^multi-(?P<a>[^_]+)_(?P<b>[^.]+)\.[^.]+$",
        fields=[
            (FieldID.COMMENTS.name, "$a"),
            (FieldID.COMMENTS.name, "$b"),
        ],
    )

    preview = preview_paths_to_fields(library, [rule])
    assert len(preview) == 1
    # Should propose two updates for the same key, in order
    assert preview[0].updates == [
        (FieldID.COMMENTS.name, "foo"),
        (FieldID.COMMENTS.name, "bar"),
    ]

    applied = apply_paths_to_fields(library, preview, create_missing_field_types=True)
    assert applied == 2

    e = unwrap(library.get_entry_full(eid))
    comment_values = [f.value or "" for f in e.fields if f.type_key == FieldID.COMMENTS.name]
    assert sorted(comment_values) == ["bar", "foo"]


def test_apply_paths_to_fields_allow_existing_appends(library: Library):
    folder = unwrap(library.folder)

    entry = Entry(folder=folder, path=Path("existing/NewSeries-extra.jpg"), fields=[])
    [eid] = library.add_entries([entry])
    assert library.add_field_to_entry(eid, field_id=FieldID.SERIES.name, value="Existing Series")

    rule = PathFieldRule(
        pattern=r"^existing/(?P<series>[^-]+)-(?P<suffix>[^.]+)\.[^.]+$",
        fields=[(FieldID.SERIES.name, "$series")],
    )

    preview = preview_paths_to_fields(library, [rule], only_unset=False)
    assert preview, "Expected preview to include updates even when field already set"

    applied_without = apply_paths_to_fields(
        library,
        preview,
        create_missing_field_types=True,
        allow_existing=False,
    )
    assert applied_without == 0
    entry_state = unwrap(library.get_entry_full(eid))
    values = [f.value or "" for f in entry_state.fields if f.type_key == FieldID.SERIES.name]
    assert values == ["Existing Series"]

    preview = preview_paths_to_fields(library, [rule], only_unset=False)
    applied_with = apply_paths_to_fields(
        library,
        preview,
        create_missing_field_types=True,
        allow_existing=True,
    )
    assert applied_with == 1
    entry_state = unwrap(library.get_entry_full(eid))
    values = [f.value or "" for f in entry_state.fields if f.type_key == FieldID.SERIES.name]
    assert sorted(values) == ["Existing Series", "NewSeries"]


def test_iter_preview_paths_to_fields_reports_progress(library: Library):
    folder = unwrap(library.folder)

    entries = [
        Entry(folder=folder, path=Path("progress/alpha_01.jpg"), fields=[]),
        Entry(folder=folder, path=Path("progress/beta_02.jpg"), fields=[]),
    ]
    library.add_entries(entries)

    rule = PathFieldRule(
        pattern=r"^progress/(?P<name>[^_]+)_(?P<page>\d+)\.[^.]+$",
        fields=[
            (FieldID.SERIES.name, "$name"),
            ("page_number", "$page"),
        ],
    )

    events = list(iter_preview_paths_to_fields(library, [rule], only_unset=False))
    assert events, "Expected progress events to be emitted"

    totals = {evt.total for evt in events if evt.total is not None}
    assert totals == {library.entry_count()}
    assert any(evt.update is not None for evt in events)


def test_iter_preview_paths_to_fields_stop(library: Library):
    folder = unwrap(library.folder)

    entries = [
        Entry(folder=folder, path=Path("stop/foo_01.jpg"), fields=[]),
        Entry(folder=folder, path=Path("stop/bar_02.jpg"), fields=[]),
    ]
    library.add_entries(entries)

    rule = PathFieldRule(
        pattern=r"^stop/(?P<stem>[^_]+)_(?P<page>\d+)\.[^.]+$",
        fields=[(FieldID.SERIES.name, "$stem")],
    )

    seen: list[int] = []

    def should_cancel() -> bool:
        return len(seen) >= 1

    for evt in iter_preview_paths_to_fields(
        library,
        [rule],
        only_unset=False,
        cancel_callback=should_cancel,
    ):
        seen.append(evt.index)

    assert seen == [1]
