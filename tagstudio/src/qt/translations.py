from pathlib import Path
from typing import Callable

import structlog
import ujson

logger = structlog.get_logger(__name__)

DEFAULT_TRANSLATION = "en"


class Translator:
    _default_strings: dict[str, str]
    _strings: dict[str, str] = {}
    _lang: str = DEFAULT_TRANSLATION

    def __init__(self):
        self._default_strings = self.__get_translation_dict(DEFAULT_TRANSLATION)

    def __get_translation_dict(self, lang: str) -> dict[str, str]:
        with open(
            Path(__file__).parents[2] / "resources" / "translations" / f"{lang}.json",
            encoding="utf-8",
        ) as f:
            return ujson.loads(f.read())

    def change_language(self, lang: str):
        self._lang = lang
        self._strings = self.__get_translation_dict(lang)

    def translate_with_setter(self, setter: Callable[[str], None], key: str, **kwargs):
        """Calls `setter` everytime the language changes and passes the translated string for `key`.

        Also formats the translation with the given keyword arguments.
        """
        # TODO replace calls to this method with direct calls to setter
        setter(Translations[key].format(**kwargs))

    def __getitem__(self, key: str) -> str:
        return self._strings.get(key) or self._default_strings.get(key) or f"[{key}]"


Translations = Translator()
