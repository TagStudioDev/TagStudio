from collections import defaultdict
from pathlib import Path
from platform import system
from typing import Any

import structlog
import ujson

logger = structlog.get_logger(__name__)

DEFAULT_TRANSLATION = "en"

LANGUAGES = {
    # "Cantonese (Traditional)": "yue_Hant",  # Empty
    "Chinese (Simplified)": "zh_Hans",
    "Chinese (Traditional)": "zh_Hant",
    # "Czech": "cs",  # Minimal
    # "Danish": "da",  # Minimal
    "Dutch": "nl",
    "English": "en",
    "Filipino": "fil",
    "French": "fr",
    "German": "de",
    "Hungarian": "hu",
    # "Italian": "it",  # Minimal
    "Japanese": "ja",
    "Norwegian Bokmål": "nb_NO",
    "Polish": "pl",
    "Portuguese (Brazil)": "pt_BR",
    # "Portuguese (Portugal)": "pt",  # Empty
    "Russian": "ru",
    "Spanish": "es",
    "Swedish": "sv",
    "Tamil": "ta",
    "Toki Pona": "tok",
    "Turkish": "tr",
    "Viossa": "qpv",
}


class Translator:
    _default_strings: dict[str, str]
    _strings: dict[str, str] = {}
    __lang: str = DEFAULT_TRANSLATION

    def __init__(self):
        self._default_strings = self.__get_translation_dict(DEFAULT_TRANSLATION)

    def __get_translation_dict(self, lang: str) -> dict[str, str]:
        try:
            with open(
                Path(__file__).parents[1] / "resources" / "translations" / f"{lang}.json",
                encoding="utf-8",
            ) as f:
                return ujson.loads(f.read())
        except FileNotFoundError:
            return self._default_strings

    def change_language(self, lang: str):
        self.__lang = lang
        self._strings = self.__get_translation_dict(lang)
        if system() == "Darwin":
            for k, v in self._strings.items():
                self._strings[k] = (
                    v.replace("&&", "<ESC_AMP>").replace("&", "", 1).replace("<ESC_AMP>", "&&")
                )

    def __format(self, text: str, **kwargs) -> str:
        try:
            return text.format(**kwargs)
        except (KeyError, ValueError):
            logger.error(
                "[Translations] Error while formatting translation.",
                text=text,
                kwargs=kwargs,
                language=self.__lang,
            )
            params: defaultdict[str, Any] = defaultdict(lambda: "{unknown_key}")
            params.update(kwargs)
            return text.format_map(params)

    def format(self, key: str, **kwargs) -> str:
        return self.__format(self[key], **kwargs)

    def __getitem__(self, key: str) -> str:
        return self._strings.get(key) or self._default_strings.get(key) or f"[{key}]"

    @property
    def current_language(self) -> str:
        return self.__lang


Translations = Translator()
