import string
from pathlib import Path

import ujson as json

CWD = Path(__file__).parent
TRANSLATION_DIR = CWD / ".." / "resources" / "translations"


def find_format_keys(format_string: str) -> set[str]:
    formatter = string.Formatter()
    return set([field[1] for field in formatter.parse(format_string) if field[1] is not None])


def foreach_translation(callback):
    with open(TRANSLATION_DIR / "en.json", encoding="utf-8") as f:
        default_translation = json.loads(f.read())
    for translation_path in TRANSLATION_DIR.glob("*.json"):
        with open(translation_path, encoding="utf-8") as f:
            translation = json.load(f)
        callback(default_translation, translation, translation_path)


def test_validate_format_keys():
    def validate_format_keys(default_translation: dict, translation: dict, translation_path: Path):
        for key in default_translation:
            if key not in translation:
                continue
            default_keys = find_format_keys(default_translation[key])
            translation_keys = find_format_keys(translation[key])
            assert default_keys.issuperset(
                translation_keys
            ), f"Translation {translation_path.name} for key {key} is using an invalid format key"
            assert translation_keys.issuperset(
                default_keys
            ), f"Translation {translation_path.name} for key {key} is missing format keys"

    foreach_translation(validate_format_keys)


def test_translation_completeness():
    def check_completeness(default_translation: dict, translation: dict, translation_path: Path):
        assert set(default_translation.keys()).issubset(
            translation.keys()
        ), f"Translation {translation_path.name} is missing keys"
        assert set(default_translation.keys()).issuperset(
            translation.keys()
        ), f"Translation {translation_path.name} has unnecessary keys"

    foreach_translation(check_completeness)
