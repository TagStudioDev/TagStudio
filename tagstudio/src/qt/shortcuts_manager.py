from collections.abc import Sequence
from functools import partial
from typing import TYPE_CHECKING, overload

from PySide6.QtCore import QKeyCombination, QMetaObject, QObject, QSettings, Qt, Signal
from PySide6.QtGui import QAction, QKeySequence, QShortcut
from PySide6.QtWidgets import QApplication

from .helpers.ini_helpers import IniKey
from .qt_logger import logger

if TYPE_CHECKING:
    from .main_window import UIMainWindow


_shortcuts: list["Shortcut"] = []
"""List of all the shortcuts."""


class Shortcut(QShortcut):
    key_changed = Signal(list)
    """Emits a list of :class:`QKeySequence` when the shortcut keys are changed or set."""

    def __init__(
        self,
        setting_name: IniKey,
        default_shortcuts: Sequence[QKeySequence | QKeySequence.StandardKey | Qt.Key],
        parent: QObject,
    ) -> None:
        super().__init__(parent)
        self._connected_actions_connections: dict[QAction, QMetaObject.Connection] = {}
        """Contains all the actions that are connected to the Shortcut instance."""

        _default_shortcuts = [QKeySequence(key) for key in default_shortcuts]
        self.setKeys(_default_shortcuts, save=False)
        self.setProperty("default_shortcuts", _default_shortcuts)
        self.setProperty("setting_name", setting_name)
        _load_shortcuts(self)
        _shortcuts.append(self)
        self.destroyed.connect(partial(_shortcuts.remove, self))

    def setKey(  # noqa: N802
        self,
        key: QKeySequence | QKeyCombination | QKeySequence.StandardKey | str | int,
        save: bool = True,
    ) -> None:
        super().setKey(key)
        self.key_changed.emit(self.keys())
        if save:
            _save_shortcuts(self)

    @overload
    def setKeys(self, key: QKeySequence.StandardKey, save: bool = True) -> None: ...
    @overload
    def setKeys(self, keys: Sequence[QKeySequence], save: bool = True) -> None: ...
    def setKeys(self, *args, save: bool = True, **kwargs) -> None:  # noqa: N802
        super().setKeys(*args, **kwargs)
        self.key_changed.emit(self.keys())
        if save:
            _save_shortcuts(self)

    def connect_action(self, action: QAction) -> None:
        """Connects the specified QAction to the Shortcut instance.

        Connects the specified QAction's setShortcuts to the key_changed signal of the Shortcut
        instance, stores the connection, and ensures the action is properly disconnected when
        destroyed.
        Disables the current Shortcut instance, and sets the action's shortcut to the Shortcut
        instance's current keys.

        Args:
            action (QAction): The QAction to connect to.

        Returns:
            None
        """
        connection = self.key_changed.connect(action.setShortcuts)
        action.destroyed.connect(partial(self.disconnect_action, action))
        action.setShortcuts(self.keys())

        self._connected_actions_connections[action] = connection
        self.setEnabled(False)

    def disconnect_action(self, action: QAction) -> None:
        """Disconnects the specified QAction from the key_changed signal of the Shortcut instance.

        Args:
            action (QAction): The QAction to disconnect from.

        Returns:
            None
        """
        if action in self._connected_actions_connections:
            connection = self._connected_actions_connections.pop(action)
            self.key_changed.disconnect(connection)
        else:
            logger.warning(f"Failed to disconnect {action}. seems it's not connected to {self}.")

        if not self._connected_actions_connections:
            self.setEnabled(True)


class DefaultShortcuts:
    """Creates and manages default shortcuts for the application.

    Returns the singleton instance of DefaultShortcuts, initialized with standard and custom
    shortcuts for the main window.
    Raises an exception if accessed before being initialized with a main window.
    """

    _instance: "DefaultShortcuts | None" = None

    def __new__(cls, main_window: "UIMainWindow | None" = None):
        if DefaultShortcuts._instance is None:
            if main_window is None:
                raise Exception("DefaultShortcuts accessed before initialized with a main window.")
            DefaultShortcuts._instance = super().__new__(cls)

            # region standard shorcuts
            cls.OPEN = Shortcut(IniKey("Open"), (QKeySequence.StandardKey.Open,), main_window)
            cls.SAVE = Shortcut(IniKey("Save"), (QKeySequence.StandardKey.Save,), main_window)
            cls.SAVE_AS = Shortcut(
                IniKey("Save_As"), (QKeySequence.StandardKey.SaveAs,), main_window
            )
            cls.REFRESH = Shortcut(
                IniKey("Refresh"), (QKeySequence.StandardKey.Refresh,), main_window
            )
            cls.SELECT_ALL = Shortcut(
                IniKey("Select_All"), (QKeySequence.StandardKey.SelectAll,), main_window
            )
            cls.DESELECT = Shortcut(
                IniKey("Deselect"),
                (QKeySequence.StandardKey.Deselect, Qt.Key.Key_Escape),
                main_window,
            )
            # endregion

            # region custom shortcuts
            cls.NEW_TAG = Shortcut(
                IniKey("New_Tag"), (QKeySequence.fromString("ctrl+t"),), main_window
            )
            cls.CLOSE_LIBRARY = Shortcut(
                IniKey("Close_Library"), (QKeySequence.fromString("ctrl+w"),), main_window
            )
            # endregion

        return DefaultShortcuts._instance


def _get_settings() -> QSettings | None:
    # region XXX: temporarily getting settings from QApplication.property("driver")
    instance = QApplication.instance()
    if instance is None:
        return None
    driver = instance.property("driver")
    if driver is None:
        return None
    settings: QSettings = driver.settings
    # endregion
    return settings


def _save_shortcuts(shortcut: Shortcut | None = None) -> None:
    """Save the keys of the specified `Shortcut` or all `Shortcut`s in settings.

    If no `shortcut` is specified, saves all the `shortcut`'s keys in settings.

    Checks if the shortcut keys are the same as the default shortcuts. Removes the settings entry if
    they are. Otherwise, saves the shortcut keys in settings.

    Args:
        shortcut (Shortcut | None): The shortcut for which keys need to be saved. Defaults to None.

    Returns:
        None
    """
    settings = _get_settings()
    if settings is None:
        return

    shortcuts = {shortcut} if shortcut is not None else _shortcuts

    settings.beginGroup("Shortcuts")
    for shortcut in shortcuts:
        default_key_sequences: Sequence[QKeySequence] = shortcut.property("default_shortcuts")
        current_key_sequences = shortcut.keys()

        # check if current shortcuts and default shortcuts are same.
        if (len(current_key_sequences) == len(default_key_sequences)) and all(
            any(
                (dks.matches(cks) is QKeySequence.SequenceMatch.ExactMatch)
                for cks in current_key_sequences
            )
            for dks in default_key_sequences
        ):
            # if they are same, remove the entry from settings.
            settings.remove(shortcut.property("setting_name"))
        else:
            # if they are different, save the shortcuts in settings.
            settings.setValue(
                shortcut.property("setting_name"), [ks.toString() for ks in current_key_sequences]
            )

    settings.endGroup()
    settings.sync()


def _load_shortcuts(shortcut: Shortcut | None = None) -> None:
    """Load and assigns the keys of the specified `Shortcut` or all `Shortcut`s from settings.

    If no `shortcut` is specified, loads all the `shortcut`'s keys from settings.

    Args:
        shortcut (Shortcut | None): The shortcut for which keys need to be loaded. Defaults to None.

    Returns:
        None
    """
    settings = _get_settings()
    if settings is None:
        return

    shortcuts = {shortcut} if shortcut is not None else _shortcuts

    settings.beginGroup("Shortcuts")

    for shortcut in shortcuts:
        _keys = settings.value(shortcut.property("setting_name"), None)

        if isinstance(_keys, str):
            key_sequences = [QKeySequence.fromString(_keys)]
        elif isinstance(_keys, list):
            key_sequences = [QKeySequence.fromString(ks) for ks in _keys]
        else:
            continue

        # TODO: check if the key sequences are valid. warn if not.

        shortcut.setKeys(key_sequences, save=False)

    settings.endGroup()


def is_shortcut_available(shortcut: QKeySequence) -> bool:
    """Checks if a given shortcut is available for use.

    Args:
        shortcut (QKeySequence): The shortcut to check availability for.

    Returns:
        bool: True if the shortcut is available, False otherwise.
    """
    for _shortcut in _shortcuts:
        for key in _shortcut.keys():  # noqa: SIM118 (https://github.com/astral-sh/ruff/issues/12578)
            if key.matches(shortcut) is QKeySequence.SequenceMatch.ExactMatch:
                return False
    return True


def is_settings_name_available(name: str) -> bool:
    """Checks if a given settings name is available for use.

    Args:
        name (str): The name to check availability for.

    Returns:
        bool: True if the name is available, False otherwise.
    """
    return all(sc.property("setting_name").lower() != name.lower() for sc in _shortcuts)
