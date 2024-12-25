from pathlib import Path
from typing import Callable

import ujson
from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QLabel, QMenu, QMessageBox, QPushButton

from .helpers.qbutton_wrapper import QPushButtonWrapper

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
        with open(
            Path(__file__).parents[2] / "resources" / "translations" / f"{lang}.json",
            encoding="utf-8",
        ) as f:
            return ujson.loads(f.read())

    def change_language(self, lang: str):
        translated = self.__get_translation_dict(lang)
        for k in self._strings:
            self._strings[k].value = translated.get(k, None)

    def translate_qobject(self, widget: QObject, key: str, **kwargs):
        """Translates the text of the QObject using :func:`translate_with_setter`."""
        if isinstance(widget, (QLabel, QAction, QPushButton, QMessageBox, QPushButtonWrapper)):
            self.translate_with_setter(widget.setText, key, **kwargs)
        elif isinstance(widget, (QMenu)):
            self.translate_with_setter(widget.setTitle, key, **kwargs)
        else:
            raise RuntimeError

    def translate_with_setter(self, setter: Callable[[str], None], key: str, **kwargs):
        """Calls `setter` everytime the language changes and passes the translated string for `key`.

        Also formats the translation with the given keyword arguments.
        """

        def set_text(text: str):
            setter(text.format(**kwargs))

        if key in self._strings:
            self._strings[key].changed.connect(set_text)
        set_text(self.translate_formatted(key, **kwargs))

    def translate_formatted(self, key: str, **kwargs) -> str:
        return self[key].format(**kwargs)

    def __getitem__(self, key: str) -> str:
        # return "???"
        return self._strings[key].value if key in self._strings else "Not Translated"


Translations = Translator()
Translations.change_language("de")
