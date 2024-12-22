from pathlib import Path

import ujson
from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QLabel, QPushButton

DEFAULT_TRANSLATION = "en"


class TranslatedString(QObject):
    changed = Signal(str)

    __default_value: str
    __value: str | None = None

    def __init__(self, value: str):
        super().__init__()
        self.__default_value = value

    @property
    def value(self) -> str:
        return self.__value or self.__default_value

    @value.setter
    def value(self, value: str):
        if self.__value != value:
            self.__value = value
            self.changed.emit(self.__value)


class Translator:
    _strings: dict[str, TranslatedString] = {}

    def __init__(self):
        for k, v in self.__get_translation_dict(DEFAULT_TRANSLATION).items():
            self._strings[k] = TranslatedString(v)

    def __get_translation_dict(self, lang: str) -> dict[str, str]:
        with open(Path(__file__).parents[2] / "resources" / "translations" / f"{lang}.json") as f:
            return ujson.loads(f.read())

    def change_language(self, lang: str):
        translated = self.__get_translation_dict(lang)
        for k in self._strings:
            self._strings[k].value = translated.get(k, None)

    def translate_widget(self, widget: QObject, key: str):
        if isinstance(widget, (QLabel, QAction, QPushButton)):
            if key in self._strings:
                self._strings[key].changed.connect(widget.setText)
            widget.setText(self.translate(key))
        else:
            raise RuntimeError

    def translate(self, key: str) -> str:
        return self._strings[key].value if key in self._strings else "Not Translated"


Translations = Translator()
