# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: MIT


from pathlib import Path

import pytest

from tagstudio.core.utils.encoding import detect_char_encoding


@pytest.mark.parametrize(
    "text",
    [
        "Hello world 😀\n",
        "Notes 🎉🎉 for the party\nsecond line\n",
        "Grüße aus Köln 👋\n",
    ],
)
def test_utf8_with_emoji_is_detected_as_utf8(tmp_path: Path, text: str):
    path = tmp_path / "emoji.txt"
    path.write_bytes(text.encode("utf-8"))

    encoding = detect_char_encoding(path)

    assert encoding == "utf-8"
    assert path.read_text(encoding=encoding) == text


def test_non_utf8_file_falls_back_to_detection(tmp_path: Path):
    text = "Ceci est un fichier en français, enregistré en Latin-1. " * 20
    path = tmp_path / "latin1.txt"
    path.write_bytes(text.encode("latin-1"))

    encoding = detect_char_encoding(path)

    assert encoding is not None
    assert encoding.lower() != "utf-8"
    assert path.read_bytes().decode(encoding) == text
