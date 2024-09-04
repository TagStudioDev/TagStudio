# Copyright (C) 2024 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio

from PySide6.QtCore import QObject, QTranslator
from pathlib import Path
from json import loads


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
        if (translationDir / (language + "_" + country + ".ini")).exists():
            file = open(
                translationDir / (language + "_" + country + ".ini"), encoding="utf-8"
            )
        elif (translationDir / (language + ".ini")).exists():
            file = open(translationDir / (language + ".ini"), encoding="utf-8")
        if file is None:
            return False

        for line in file.readlines():
            if line.startswith("#") or line == "\n":
                continue
            identifier, translation = line.split("=", 1)
            self.translations[identifier] = loads(translation)

        file.close()
        return True
