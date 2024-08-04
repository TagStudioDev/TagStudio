# Copyright (C) 2024 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio


from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import (
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QStyledItemDelegate,
    QLineEdit,
    QComboBox,
    QLabel,
)

from src.core.library import Library
from src.qt.widgets.panel import PanelWidget


class FileExtensionItemDelegate(QStyledItemDelegate):
    def setModelData(self, editor, model, index):
        if isinstance(editor, QLineEdit):
            if editor.text() and not editor.text().startswith("."):
                editor.setText(f".{editor.text()}")
        super().setModelData(editor, model, index)


class FileExtensionModal(PanelWidget):
    done = Signal()

    def __init__(self, library: "Library"):
        super().__init__()
        # Initialize Modal =====================================================
        self.lib = library
        self.setWindowTitle("File Extensions")
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setMinimumSize(240, 400)
        self.root_layout = QVBoxLayout(self)
        self.root_layout.setContentsMargins(6, 6, 6, 6)

        # Create Table Widget --------------------------------------------------
        self.table = QTableWidget(len(self.lib.ext_list), 1)
        self.table.horizontalHeader().setVisible(False)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setItemDelegate(FileExtensionItemDelegate())

        # Create "Add Button" Widget -------------------------------------------
        self.add_button = QPushButton()
        self.add_button.setText("&Add Extension")
        self.add_button.clicked.connect(self.add_item)
        self.add_button.setDefault(True)
        self.add_button.setMinimumWidth(100)

        # Create Mode Widgets --------------------------------------------------
        self.mode_widget = QWidget()
        self.mode_layout = QHBoxLayout(self.mode_widget)
        self.mode_layout.setContentsMargins(0, 0, 0, 0)
        self.mode_layout.setSpacing(12)
        self.mode_label = QLabel()
        self.mode_label.setText("List Mode:")
        self.mode_combobox = QComboBox()
        self.mode_combobox.setEditable(False)
        self.mode_combobox.addItem("Exclude")
        self.mode_combobox.addItem("Include")
        self.mode_combobox.setCurrentIndex(0 if self.lib.is_exclude_list else 1)
        self.mode_combobox.currentIndexChanged.connect(
            lambda i: self.update_list_mode(i)
        )
        self.mode_layout.addWidget(self.mode_label)
        self.mode_layout.addWidget(self.mode_combobox)
        self.mode_layout.setStretch(1, 1)

        # Add Widgets To Layout ------------------------------------------------
        self.root_layout.addWidget(self.mode_widget)
        self.root_layout.addWidget(self.table)
        self.root_layout.addWidget(
            self.add_button, alignment=Qt.AlignmentFlag.AlignCenter
        )

        # Finalize Modal -------------------------------------------------------
        self.refresh_list()

    def update_list_mode(self, mode: int):
        """
        Update the mode of the extension list: "Exclude" or "Include".

        Args:
            mode (int): The list mode, given by the index of the mode inside
                the mode combobox. 0 for "Exclude", 1 for "Include".
        """
        if mode == 0:
            self.lib.is_exclude_list = True
        elif mode == 1:
            self.lib.is_exclude_list = False

    def refresh_list(self):
        for i, ext in enumerate(self.lib.ext_list):
            self.table.setItem(i, 0, QTableWidgetItem(ext))

    def add_item(self):
        self.table.insertRow(self.table.rowCount())

    def save(self):
        self.lib.ext_list.clear()
        for i in range(self.table.rowCount()):
            ext = self.table.item(i, 0)
            if ext and ext.text():
                self.lib.ext_list.append(ext.text().lower())
