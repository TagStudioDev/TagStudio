from pathlib import Path
from typing import Callable

import structlog
import ujson

logger = structlog.get_logger(__name__)

DEFAULT_TRANSLATION = "en"


class TranslatedString:
    __default_value: str
    __value: str | None = None

    def __init__(self, value: str):
        super().__init__()
        self.__default_value = value

    @property
    def value(self) -> str:
        return self.__value or self.__default_value

    @value.setter
    def value(self, value: str | None):
        self.__value = value


class Translator:
    _strings: dict[str, TranslatedString] = {}
    _lang: str = DEFAULT_TRANSLATION

    def __init__(self):
        for k, v in self.__get_translation_dict(DEFAULT_TRANSLATION).items():
            self._strings[k] = TranslatedString(v)

    def __get_translation_dict(self, lang: str) -> dict[str, str]:
        with open(
            Path(__file__).parents[2] / "resources" / "translations" / f"{lang}.json",
            encoding="utf-8",
        ) as f:
            return ujson.loads(f.read())

    def change_language(self, lang: str):
        self._lang = lang
        translated = self.__get_translation_dict(lang)
        for k in self._strings:
            self._strings[k].value = translated.get(k, None)

    def translate_with_setter(self, setter: Callable[[str], None], key: str, **kwargs):
        """Calls `setter` everytime the language changes and passes the translated string for `key`.

        Also formats the translation with the given keyword arguments.
        """
        # TODO replace calls to this method with direct calls to setter
        setter(Translations[key].format(**kwargs))

    def __getitem__(self, key: str) -> str:
        return self._strings[key].value if key in self._strings else f"[{key}]"


Translations = Translator()
