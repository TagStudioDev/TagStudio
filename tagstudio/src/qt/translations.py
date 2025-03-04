from collections import defaultdict
from pathlib import Path

import structlog
import ujson

logger = structlog.get_logger(__name__)

DEFAULT_TRANSLATION = "en"


class ErrorlessFormatString(str):
    __translator: "Translator"

    def __new__(cls, translator: "Translator", object: object = ""):
        obj = super().__new__(cls, object)
        obj.__translator = translator
        return obj

    def format(self, *args: object, **kwargs: object) -> str:
        try:
            return super().format(*args, **kwargs)
        except KeyError:
            logger.error(
                "[Translations] Error while formatting translation.",
                text=self,
                language=self.__translator._lang,
                kwargs=kwargs,
            )
            params: defaultdict = defaultdict(lambda: "{missing_key}")
            params.update(kwargs)
            return super().format_map(params)


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

    def __getitem__(self, key: str) -> str:
        return ErrorlessFormatString(
            self, self._strings.get(key) or self._default_strings.get(key) or f"[{key}]"
        )


Translations = Translator()
