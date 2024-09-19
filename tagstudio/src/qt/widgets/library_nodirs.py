from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class LibraryNoFolders(QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.lib_nofolders_layout = QVBoxLayout(self)
        self.lib_nofolders_layout.setContentsMargins(0, 0, 0, 0)
        self.lib_nofolders_layout.setSpacing(0)
        self.lib_nofolders_label = QLabel(self)
        self.lib_nofolders_label.setObjectName("lib_nofolders_label")
        self.lib_nofolders_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lib_nofolders_label.setText("No folders found in library.")
        self.lib_nofolders_layout.addWidget(self.lib_nofolders_label)
