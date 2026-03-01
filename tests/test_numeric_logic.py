from pathlib import Path

from tagstudio.core.library.alchemy.fields import NumericField
from tagstudio.core.library.alchemy.library import Library
from tagstudio.core.library.alchemy.models import Entry
from tagstudio.core.utils.types import unwrap


def test_numeric_field_stores_numeric_data(library: Library):
    """REQ-01"""
    entry = Entry(
        path=Path("test_numeric.txt"),
        folder=unwrap(library.folder),
        fields=[NumericField(type_key="QUANTITY", value=100)],
    )

    entry_id = library.add_entries([entry])[0]
    refreshed = unwrap(library.get_entry_full(entry_id))

    assert refreshed.numeric_fields[0].value == 100


def test_add_numeric_field_to_entry(library: Library):
    """REQ-01a"""

    entry = Entry(
        path=Path("test_add.txt"),
        folder=unwrap(library.folder),
        fields=[NumericField(type_key="RATING", value=5)],
    )

    ids = library.add_entries([entry])
    assert len(ids) == 1


def test_numeric_field_stores_integer(library: Library):
    """REQ-01c"""

    entry = Entry(
        path=Path("test_int.txt"),
        folder=unwrap(library.folder),
        fields=[NumericField(type_key="SCORE", value=42)],
    )

    entry_id = library.add_entries([entry])[0]
    refreshed = unwrap(library.get_entry_full(entry_id))

    assert refreshed.numeric_fields[0].value == 42
    assert isinstance(refreshed.numeric_fields[0].value, int)


def test_numeric_field_handles_floats(library: Library):
    """REQ-01d"""
    entry = Entry(
        path=Path("test_float.txt"),
        folder=unwrap(library.folder),
        fields=[NumericField(type_key="PRICE", value=19.99)],
    )

    entry_id = library.add_entries([entry])[0]
    refreshed = unwrap(library.get_entry_full(entry_id))

    assert refreshed.numeric_fields[0].value == 19.99
    assert isinstance(refreshed.numeric_fields[0].value, float)


def test_update_numeric_field(library: Library):
    """REQ-01e"""

    entry = Entry(
        path=Path("test_update.txt"),
        folder=unwrap(library.folder),
        fields=[NumericField(type_key="LEVEL", value=1)],
    )

    entry_id = library.add_entries([entry])[0]
    refreshed_entry = unwrap(library.get_entry_full(entry_id))
    field_to_update = refreshed_entry.numeric_fields[0]

    library.update_entry_field(entry_id, field_to_update, 10)

    updated_entry = unwrap(library.get_entry_full(entry_id))
    assert updated_entry.numeric_fields[0].value == 10


def test_numeric_comparison_query(library: Library):
    """REQ-01f"""

    e1 = Entry(
        path=Path("low.txt"),
        folder=unwrap(library.folder),
        fields=[NumericField(type_key="VAL", value=10)],
    )
    e2 = Entry(
        path=Path("high.txt"),
        folder=unwrap(library.folder),
        fields=[NumericField(type_key="VAL", value=100)],
    )

    library.add_entries([e1, e2])

    all_entries = list(library.all_entries(with_joins=True))
    vals = [e.numeric_fields[0].value for e in all_entries if e.numeric_fields]

    assert max(vals) == 100
    assert min(vals) == 10
