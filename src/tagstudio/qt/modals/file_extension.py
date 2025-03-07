# Copyright (C) 2024 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio


from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QStyledItemDelegate,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)
from src.core.enums import LibraryPrefs
from src.core.library import Library
from src.qt.translations import Translations
from src.qt.widgets.panel import PanelWidget


class FileExtensionItemDelegate(QStyledItemDelegate):
    def setModelData(self, editor, model, index):  # noqa: N802
        if isinstance(editor, QLineEdit) and editor.text() and not editor.text().startswith("."):
            editor.setText(f".{editor.text()}")
        super().setModelData(editor, model, index)


class FileExtensionModal(PanelWidget):
    done = Signal()

    def __init__(self, library: "Library"):
        super().__init__()
        # Initialize Modal =====================================================
        self.lib = library
        self.setWindowTitle(Translations["ignore_list.title"])
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setMinimumSize(240, 400)
        self.root_layout = QVBoxLayout(self)
        self.root_layout.setContentsMargins(6, 6, 6, 6)

        # Create Table Widget --------------------------------------------------
        self.table = QTableWidget(len(self.lib.prefs(LibraryPrefs.EXTENSION_LIST)), 1)
        self.table.horizontalHeader().setVisible(False)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setItemDelegate(FileExtensionItemDelegate())

        # Create "Add Button" Widget -------------------------------------------
        self.add_button = QPushButton(Translations["ignore_list.add_extension"])
        self.add_button.clicked.connect(self.add_item)
        self.add_button.setDefault(True)
        self.add_button.setMinimumWidth(100)

        # Create Mode Widgets --------------------------------------------------
        self.mode_widget = QWidget()
        self.mode_layout = QHBoxLayout(self.mode_widget)
        self.mode_layout.setContentsMargins(0, 0, 0, 0)
        self.mode_layout.setSpacing(12)
        self.mode_label = QLabel(Translations["ignore_list.mode.label"])
        self.mode_combobox = QComboBox()
        self.mode_combobox.setEditable(False)
        self.mode_combobox.addItem("")
        self.mode_combobox.addItem("")
        self.mode_combobox.setItemText(0, Translations["ignore_list.mode.include"])
        self.mode_combobox.setItemText(1, Translations["ignore_list.mode.exclude"])

        is_exclude_list = int(bool(self.lib.prefs(LibraryPrefs.IS_EXCLUDE_LIST)))

        self.mode_combobox.setCurrentIndex(is_exclude_list)
        self.mode_combobox.currentIndexChanged.connect(lambda i: self.update_list_mode(i))
        self.mode_layout.addWidget(self.mode_label)
        self.mode_layout.addWidget(self.mode_combobox)
        self.mode_layout.setStretch(1, 1)

        # Add Widgets To Layout ------------------------------------------------
        self.root_layout.addWidget(self.mode_widget)
        self.root_layout.addWidget(self.table)
        self.root_layout.addWidget(self.add_button, alignment=Qt.AlignmentFlag.AlignCenter)

        # Finalize Modal -------------------------------------------------------
        self.refresh_list()

    def update_list_mode(self, mode: int):
        """Update the mode of the extension list: "Exclude" or "Include".

        Args:
            mode (int): The list mode, given by the index of the mode inside
                the mode combobox. 1 for "Exclude", 0 for "Include".
        """
        self.lib.set_prefs(LibraryPrefs.IS_EXCLUDE_LIST, bool(mode))

    def refresh_list(self):
        for i, ext in enumerate(self.lib.prefs(LibraryPrefs.EXTENSION_LIST)):
            self.table.setItem(i, 0, QTableWidgetItem(ext))

    def add_item(self):
        self.table.insertRow(self.table.rowCount())

    def save(self):
        extensions = []
        for i in range(self.table.rowCount()):
            ext = self.table.item(i, 0)
            if ext and ext.text().strip():
                extensions.append(ext.text().strip().lstrip(".").lower())

        # save preference
        self.lib.set_prefs(LibraryPrefs.EXTENSION_LIST, extensions)
