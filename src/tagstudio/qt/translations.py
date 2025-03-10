from collections import defaultdict
from pathlib import Path
from typing import Any

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
            Path(__file__).parents[1] / "resources" / "translations" / f"{lang}.json",
            encoding="utf-8",
        ) as f:
            return ujson.loads(f.read())

    def change_language(self, lang: str):
        self._lang = lang
        self._strings = self.__get_translation_dict(lang)

    def __format(self, text: str, **kwargs) -> str:
        try:
            return text.format(**kwargs)
        except (KeyError, ValueError):
            logger.error(
                "[Translations] Error while formatting translation.",
                text=text,
                kwargs=kwargs,
                language=self._lang,
            )
            params: defaultdict[str, Any] = defaultdict(lambda: "{unknown_key}")
            params.update(kwargs)
            return text.format_map(params)

    def format(self, key: str, **kwargs) -> str:
        return self.__format(self[key], **kwargs)

    def __getitem__(self, key: str) -> str:
        return self._strings.get(key) or self._default_strings.get(key) or f"[{key}]"


Translations = Translator()
