# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: MIT


import json
from pathlib import Path

import toml

from tagstudio.core.utils.data_file import BaseDataFile


class ExampleDataFile(BaseDataFile):
    """An example use of the BaseDataFile class."""

    name: str = "default"
    count: int = 0


def test_missing_file_loads_defaults(tmp_path: Path):
    data_file = ExampleDataFile.load(tmp_path / "data.json")

    assert data_file.name == "default"


def test_json_extension_saves_json(tmp_path: Path):
    path = tmp_path / "data.json"
    data_file = ExampleDataFile.load(path)
    data_file.name = "saved"

    data_file.save()

    assert json.loads(path.read_text(encoding="utf-8"))["name"] == "saved"


def test_toml_extension_saves_toml(tmp_path: Path):
    path = tmp_path / "data.toml"
    data_file = ExampleDataFile.load(path)
    data_file.name = "saved"

    data_file.save()

    assert toml.loads(path.read_text(encoding="utf-8"))["name"] == "saved"


def test_saved_data_file_loads_saved_values(tmp_path: Path):
    path = tmp_path / "data.json"
    data_file = ExampleDataFile.load(path)
    data_file.name = "saved"
    data_file.save()

    assert ExampleDataFile.load(path).name == "saved"


def test_malformed_json_file_loads_defaults(tmp_path: Path):
    path = tmp_path / "data.json"
    path.write_text('{"name": "saved"', encoding="utf-8")

    assert ExampleDataFile.load(path).name == "default"


def test_malformed_toml_line_loads_default_for_that_value_only(tmp_path: Path):
    path = tmp_path / "data.toml"
    path.write_text('name = "saved"\ncount = "many\n', encoding="utf-8")

    data_file = ExampleDataFile.load(path)

    assert (data_file.name, data_file.count) == ("saved", 0)


def test_file_that_cant_be_read_loads_defaults(tmp_path: Path):
    path = tmp_path / "data.json"
    path.mkdir()

    assert ExampleDataFile.load(path).name == "default"


def test_invalid_value_loads_default_for_that_value_only(tmp_path: Path):
    path = tmp_path / "data.json"
    path.write_text('{"name": "saved", "count": "many"}', encoding="utf-8")

    data_file = ExampleDataFile.load(path)

    assert (data_file.name, data_file.count) == ("saved", 0)
