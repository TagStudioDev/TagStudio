# import shutil
# from pathlib import Path
# from tempfile import TemporaryDirectory

# import pytest
# from src.core.enums import MacroID
# from src.core.library.alchemy.fields import _FieldID


# @pytest.mark.parametrize("library", [TemporaryDirectory()], indirect=True)
def test_sidecar_macro(qt_driver, library, cwd, entry_full):
    # TODO: Rework and finalize sidecar loading + macro systems.
    pass
    # entry_full.path = Path("newgrounds/foo.txt")

    # fixture = cwd / "fixtures/sidecar_newgrounds.json"
    # dst = library.library_dir / "newgrounds" / (entry_full.path.name + ".json")
    # dst.parent.mkdir()
    # shutil.copy(fixture, dst)

    # qt_driver.frame_content = [entry_full]
    # qt_driver.run_macro(MacroID.SIDECAR, entry_full.id)

    # entry = library.get_entry_full(entry_full.id)
    # new_fields = (
    #     (_FieldID.DESCRIPTION.name, "NG description"),
    #     (_FieldID.ARTIST.name, "NG artist"),
    #     (_FieldID.SOURCE.name, "https://ng.com"),
    # )
    # found = [(field.type.key, field.value) for field in entry.fields]

    # # `new_fields` should be subset of `found`
    # for field in new_fields:
    #     assert field in found, f"Field not found: {field} / {found}"

    # expected_tags = {"ng_tag", "ng_tag2"}
    # assert {x.name in expected_tags for x in entry.tags}
