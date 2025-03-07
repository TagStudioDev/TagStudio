import string
from pathlib import Path

import pytest
import ujson as json

CWD = Path(__file__).parent
TRANSLATION_DIR = CWD / ".." / "resources" / "translations"


def load_translation(filename: str) -> dict[str, str]:
    with open(TRANSLATION_DIR / filename, encoding="utf-8") as f:
        return json.load(f)


def get_translation_filenames() -> list[tuple[str]]:
    return [(a.name,) for a in TRANSLATION_DIR.glob("*.json")]


def find_format_keys(format_string: str) -> set[str]:
    formatter = string.Formatter()
    return set([field[1] for field in formatter.parse(format_string) if field[1] is not None])


@pytest.mark.parametrize(["translation_filename"], get_translation_filenames())
def test_format_key_validity(translation_filename: str):
    default_translation = load_translation("en.json")
    translation = load_translation(translation_filename)
    for key in default_translation:
        if key not in translation:
            continue
        default_keys = find_format_keys(default_translation[key])
        translation_keys = find_format_keys(translation[key])
        assert default_keys.issuperset(
            translation_keys
        ), f"Translation {translation_filename} for key {key} is using an invalid format key ({translation_keys.difference(default_keys)})"  # noqa: E501
        assert translation_keys.issuperset(
            default_keys
        ), f"Translation {translation_filename} for key {key} is missing format keys ({default_keys.difference(translation_keys)})"  # noqa: E501


@pytest.mark.parametrize(["translation_filename"], get_translation_filenames())
def test_for_unnecessary_translations(translation_filename: str):
    default_translation = load_translation("en.json")
    translation = load_translation(translation_filename)
    assert set(
        default_translation.keys()
    ).issuperset(
        translation.keys()
    ), f"Translation {translation_filename} has unnecessary keys ({set(translation.keys()).difference(default_translation.keys())})"  # noqa: E501
