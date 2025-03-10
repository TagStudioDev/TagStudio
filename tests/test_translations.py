import string
from pathlib import Path

import pytest
import ujson as json

CWD = Path(__file__).parent
TRANSLATION_DIR = CWD / ".." / "src" / "tagstudio" / "resources" / "translations"


def load_translation(filename: str) -> dict[str, str]:
    with open(TRANSLATION_DIR / filename, encoding="utf-8") as f:
        return json.load(f)


def get_translation_filenames() -> list[tuple[str]]:
    return [(a.name,) for a in TRANSLATION_DIR.glob("*.json")]


def test_translation_dir():
    assert TRANSLATION_DIR.exists()


def find_format_keys(format_string: str) -> set[str]:
    formatter = string.Formatter()
    return set([field[1] for field in formatter.parse(format_string) if field[1] is not None])


@pytest.mark.parametrize(["translation_filename"], get_translation_filenames())
def test_format_key_validity(translation_filename: str):
    default_translation = load_translation("en.json")
    translation = load_translation(translation_filename)
    invalid_keys: list[tuple[str, list[str]]] = []
    missing_keys: list[tuple[str, list[str]]] = []
    for key in default_translation:
        if key not in translation:
            continue
        default_keys = find_format_keys(default_translation[key])
        translation_keys = find_format_keys(translation[key])
        if not default_keys.issuperset(translation_keys):
            invalid_keys.append((key, list(translation_keys.difference(default_keys))))
        if not translation_keys.issuperset(default_keys):
            missing_keys.append((key, list(default_keys.difference(translation_keys))))
    assert len(invalid_keys) == 0, (
        f"Translation {translation_filename} has invalid format keys in some translations: {invalid_keys}"  # noqa: E501
    )
    assert len(missing_keys) == 0, (
        f"Translation {translation_filename} is missing format keys in some translations: {missing_keys}"  # noqa: E501
    )


@pytest.mark.parametrize(["translation_filename"], get_translation_filenames())
def test_for_unnecessary_translations(translation_filename: str):
    default_translation = load_translation("en.json")
    translation = load_translation(translation_filename)
    assert set(default_translation.keys()).issuperset(translation.keys()), (
        f"Translation {translation_filename} has unnecessary keys ({set(translation.keys()).difference(default_translation.keys())})"  # noqa: E501
    )
