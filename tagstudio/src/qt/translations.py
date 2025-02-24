from abc import abstractmethod
from pathlib import Path
from typing import Callable
from weakref import WeakSet

import structlog
import ujson
from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QLabel, QMenu, QMessageBox, QPushButton, QWidget

from .helpers.qbutton_wrapper import QPushButtonWrapper

logger = structlog.get_logger(__name__)

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
    def value(self, value: str | None):
        if self.__value != value:
            self.__value = value
            self.changed.emit(self.__value)


class Translator:
    _watchers: WeakSet["TranslationWatcher"] = WeakSet()
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

    def register_translation_watcher(self, widget: "TranslationWatcher"):
        self._watchers.add(widget)

    def change_language(self, lang: str):
        self._lang = lang
        translated = self.__get_translation_dict(lang)
        for k in self._strings:
            self._strings[k].value = translated.get(k, None)
        for w in self._watchers:
            w.update_text()

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
        # TODO: Fix so deleted Qt objects aren't referenced any longer
        # if key in self._strings:
        #     self._strings[key].changed.connect(lambda text: setter(self.__format(text, **kwargs)))
        setter(self.translate_formatted(key, **kwargs))

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
            return text

    def translate_formatted(self, key: str, **kwargs) -> str:
        return self.__format(self[key], **kwargs)

    def __getitem__(self, key: str) -> str:
        return self._strings[key].value if key in self._strings else f"[{key}]"


Translations = Translator()


class TranslationWatcher:
    def __init__(self):
        Translations.register_translation_watcher(self)

    @abstractmethod
    def update_text(self):
        pass


class TQPushButton(QPushButton, TranslationWatcher):
    def __init__(self, key: str, parent: QWidget | None = None):
        super().__init__(parent)
        self.key: str = key
        self.update_text()

    def update_text(self):
        self.setText(Translations.translate_formatted(self.key))
