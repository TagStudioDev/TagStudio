# Copyright (C) 2024 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio

from PySide6.QtCore import QObject, QTranslator
from pathlib import Path
from json import load as load_json


class TSTranslator(QTranslator):
    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.translations: dict[str, str] = {}

    def translate(
        self, context, sourceText, disambiguation: str | None = None, n: int = -1
    ) -> str:
        return self.translations.get(context + "." + sourceText.replace(" ", ""))

    def load(self, translationDir: Path, language: str, country: str = "") -> bool:
        file = None
        translations = None
        if (translationDir / (language + "_" + country + ".json")).exists():
            with open(translationDir / (language + "_" + country + ".json")) as file:
                translations = load_json(file)
        elif (translationDir / (language + ".json")).exists():
            with open(translationDir / (language + ".json")) as file:
                translations = load_json(file)
        if file is None:
            return False

        self.translations = translations
        file.close()
        return True
