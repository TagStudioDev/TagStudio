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
        if (translationDir / (language + "_" + country + ".json")).exists():
            file = load_json(  # noqa: SIM115
                translationDir / (language + "_" + country + ".json"), encoding="utf-8"
            )
        elif (translationDir / (language + ".json")).exists():
            file = load_json(translationDir / (language + ".json"), encoding="utf-8")  # noqa: SIM115
        if file is None:
            return False

        self.translations = file

        file.close()
        return True
