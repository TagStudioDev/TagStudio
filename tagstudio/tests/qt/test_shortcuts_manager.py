from pathlib import Path

import pytest
from PySide6.QtCore import QSettings
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import QApplication, QWidget
from src.qt import shortcuts_manager
from src.qt.helpers.ini_helpers import IniKey
from src.qt.shortcuts_manager import (
    DefaultShortcuts,
    Shortcut,
    _load_shortcuts,
    is_settings_name_available,
    is_shortcut_available,
)


@pytest.fixture()
def widget(qtbot) -> QWidget:
    return QWidget()


@pytest.fixture(autouse=True)
def reset__shortcuts_variable(monkeypatch):
    original_value = shortcuts_manager._shortcuts
    monkeypatch.setattr(shortcuts_manager, "_shortcuts", original_value)


@pytest.fixture(scope="module")
def setting_name():
    def generate_names():
        count = 1
        while True:
            yield f"shortcut{count}"
            count += 1

    generator = generate_names()

    yield generator.__next__


class TestDefaultShortcuts:
    @staticmethod
    def test___new__(widget):
        instance1 = DefaultShortcuts(widget)
        instance2 = DefaultShortcuts(widget)
        assert instance1 is instance2

    @staticmethod
    def test_default_shortcuts(widget):
        default_shortcuts = DefaultShortcuts(widget)
        assert isinstance(default_shortcuts.OPEN, Shortcut)
        assert isinstance(default_shortcuts.NEW_TAG, Shortcut)
        assert isinstance(default_shortcuts.SAVE, Shortcut)


class TestShortcut:
    @staticmethod
    def test___init__(widget, setting_name):
        name_1 = setting_name()
        name_2 = setting_name()
        shortcut1 = Shortcut(IniKey(name_1), (QKeySequence.fromString("ctrl+alt+o"),), widget)
        shortcut2 = Shortcut(
            IniKey(name_2),
            (QKeySequence.fromString("ctrl+1"), QKeySequence.fromString("ctrl+2")),
            widget,
        )

        assert (
            shortcut1.key().matches(QKeySequence.fromString("ctrl+alt+o"))
            is QKeySequence.SequenceMatch.ExactMatch
        )
        assert (
            shortcut2.key().matches(QKeySequence.fromString("ctrl+1"))
            is QKeySequence.SequenceMatch.ExactMatch
        )

        for shortcut, expected in zip(shortcut2.keys(), ("ctrl+1", "ctrl+2")):
            assert shortcut.matches(QKeySequence.fromString(expected))

    @staticmethod
    def test_key_changed(widget, setting_name, qtbot):
        name_1 = setting_name()

        shortcut1 = Shortcut(IniKey(name_1), (QKeySequence.fromString("ctrl+1"),), widget)
        with qtbot.waitSignal(shortcut1.key_changed, timeout=1000) as blocker:
            shortcut1.setKey(QKeySequence.fromString("ctrl+2"))

        assert (
            shortcut1.keys()[0].matches(blocker.args[0][0]) is QKeySequence.SequenceMatch.ExactMatch
        )

    @staticmethod
    def test_connect_action(widget, setting_name):
        name_1 = setting_name()

        shortcut1 = Shortcut(IniKey(name_1), (QKeySequence.fromString("ctrl+1"),), widget)
        shortcut1.connect_action(action := QAction())

        assert shortcut1.isEnabled() is False
        assert (
            action.shortcut().matches(QKeySequence.fromString("ctrl+1"))
            is QKeySequence.SequenceMatch.ExactMatch
        )

        shortcut1.setKey(QKeySequence.fromString("ctrl+2"))
        assert action.shortcut().matches(QKeySequence.fromString("ctrl+2"))

        action.destroyed.emit()

        shortcut1.setKey(QKeySequence.fromString("ctrl+3"))
        assert (
            action.shortcut().matches(QKeySequence.fromString("ctrl+2"))
            is QKeySequence.SequenceMatch.ExactMatch
        )

    @staticmethod
    def test_disconnect_action(widget, setting_name):
        name_1 = setting_name()

        shortcut1 = Shortcut(IniKey(name_1), (QKeySequence.fromString("ctrl+1"),), widget)
        shortcut1.connect_action(action1 := QAction())
        shortcut1.connect_action(action2 := QAction())
        shortcut1.setKey(QKeySequence.fromString("ctrl+2"))

        assert (
            action1.shortcut().matches(QKeySequence.fromString("ctrl+2"))
            is QKeySequence.SequenceMatch.ExactMatch
        )
        assert shortcut1.isEnabled() is False

        shortcut1.disconnect_action(action1)
        shortcut1.setKey(QKeySequence.fromString("ctrl+3"))
        assert (
            action1.shortcut().matches(QKeySequence.fromString("ctrl+2"))
            is QKeySequence.SequenceMatch.ExactMatch
        )
        assert shortcut1.isEnabled() is False

        shortcut1.disconnect_action(action2)
        assert shortcut1.isEnabled() is True


def test__load_shortcuts(tmp_path: Path, widget, setting_name):
    settings_file = tmp_path / "test_shortcuts_manager_settings.ini"

    name1, name2, name3 = setting_name(), setting_name(), setting_name()
    key1, key2, key3 = "ctrl+0", "ctrl+1", "ctrl+2"

    settings_file.write_text(
        "\n".join(
            (
                "[Shortcuts]",
                f"{name1} = {key1}",
                f"{name2} = {key2}, {key3}",
                f"{name3} = {key3}",
            )
        )
    )

    # region NOTE: temporary solution for test by making fake driver to use QSettings
    app = QApplication.instance() or QApplication([])

    class Driver:
        settings = QSettings(str(settings_file), QSettings.Format.IniFormat, app)

    app.setProperty("driver", Driver)
    # endregion

    shortcut1 = Shortcut(IniKey(name1), (QKeySequence.fromString("ctrl+alt+0"),), widget)
    shortcut2 = Shortcut(IniKey(name2), (QKeySequence.fromString("ctrl+alt+1"),), widget)
    shortcut3 = Shortcut(IniKey(name3), (QKeySequence.fromString("ctrl+alt+2"),), widget)
    _load_shortcuts()

    assert (
        shortcut1.key().matches(QKeySequence.fromString(key1))
        is QKeySequence.SequenceMatch.ExactMatch
    )
    assert (
        shortcut2.key().matches(QKeySequence.fromString(key2))
        is QKeySequence.SequenceMatch.ExactMatch
    )
    assert (
        shortcut2.keys()[1].matches(QKeySequence.fromString(key3))
        is QKeySequence.SequenceMatch.ExactMatch
    )
    assert (
        shortcut3.key().matches(QKeySequence.fromString(key3))
        is QKeySequence.SequenceMatch.ExactMatch
    )


def test__save_shortcut(tmp_path: Path, widget, setting_name):
    settings_file = tmp_path / "test_shortcuts_manager_settings.ini"

    # region NOTE: temporary solution for test by making fake driver to use QSettings
    app = QApplication.instance() or QApplication([])

    class Driver:
        settings = QSettings(settings_file.as_posix(), QSettings.Format.IniFormat, app)

    app.setProperty("driver", Driver)
    # endregion

    name1, name2, name3 = setting_name(), setting_name(), setting_name()

    shortcut1 = Shortcut(IniKey(name1), (QKeySequence.fromString("ctrl+alt+0"),), widget)
    shortcut2 = Shortcut(IniKey(name2), (QKeySequence.fromString("ctrl+alt+1"),), widget)
    shortcut3 = Shortcut(IniKey(name3), (QKeySequence.fromString("ctrl+alt+2"),), widget)

    shortcut1.setKey(QKeySequence.fromString("ctrl+1"))
    shortcut2.setKey(QKeySequence.fromString("ctrl+alt+1"))
    shortcut3.setKeys(
        [
            QKeySequence.fromString("ctrl+2"),
            QKeySequence.fromString("ctrl+,"),
            QKeySequence.fromString('ctrl+"'),
        ]
    )

    expected_lines = (
        "[Shortcuts]",
        f"{name1}=Ctrl+1",
        rf'{name3}=Ctrl+2, "Ctrl+,", Ctrl+\"',
    )

    for result, expected in zip(settings_file.read_text().splitlines(), expected_lines):
        assert result == expected


def test_is_shortcut_available(widget, setting_name):
    name1, name2 = setting_name(), setting_name()

    Shortcut(IniKey(name1), (QKeySequence.fromString("ctrl+alt+0"),), widget)
    assert is_shortcut_available(QKeySequence.fromString("ctrl+alt+0")) is False

    shortcut = Shortcut(
        IniKey(name2),
        (QKeySequence.fromString("ctrl+a"), QKeySequence.fromString("ctrl+b")),
        widget,
    )
    shortcut.setKeys((QKeySequence.fromString("ctrl+a"), QKeySequence.fromString("ctrl+c")))

    assert is_shortcut_available(QKeySequence.fromString("ctrl+a")) is False
    assert is_shortcut_available(QKeySequence.fromString("ctrl+b")) is True
    assert is_shortcut_available(QKeySequence.fromString("ctrl+c")) is False


def test_is_settings_name_available(widget, setting_name):
    unavailable, available = setting_name(), setting_name()

    Shortcut(IniKey(unavailable), (QKeySequence.fromString("ctrl+alt+0"),), widget)

    assert is_settings_name_available(unavailable) is False
    assert is_settings_name_available(available) is True
