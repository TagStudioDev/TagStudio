from pathlib import Path

from PySide6.QtWidgets import (
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
)


class LABELS:
    NO_FOLDER = "No folder selected."
    CHOOSE_NAME = "Choose Library Name"
    SELECT_FOLDER = "Select Metadata Folder"


class LibraryNameDialog(QDialog):
    chosen_path: Path | None

    def __init__(self):
        super().__init__()

        self.setFixedWidth(400)

        self.chosen_path = None

        self.setWindowTitle(LABELS.CHOOSE_NAME)

        layout = QVBoxLayout()

        label = QLabel(LABELS.CHOOSE_NAME)
        layout.addWidget(label)

        self.library_name_input = QLineEdit(self)
        self.library_name_input.textChanged.connect(self.update_storage_label)
        layout.addWidget(self.library_name_input)

        self.storage_explanation = QLabel("Select a folder where library metadata will be stored.")
        layout.addWidget(self.storage_explanation)

        choose_directory_button = QPushButton(LABELS.SELECT_FOLDER, self)
        choose_directory_button.clicked.connect(self.choose_directory)
        layout.addWidget(choose_directory_button)

        self.directory_label = QLabel(LABELS.NO_FOLDER)
        layout.addWidget(self.directory_label)

        cancel_button = QPushButton("Cancel", self)
        cancel_button.clicked.connect(self.reject)

        ok_button = QPushButton("OK", self)
        ok_button.clicked.connect(self.accept)

        button_layout = QHBoxLayout()
        button_layout.addWidget(cancel_button)
        button_layout.addWidget(ok_button)

        layout.addLayout(button_layout)
        self.setLayout(layout)

    def get_storage_path(self) -> Path:
        # return self.chosen_path / f"TS {self.get_library_name()}"
        return self.chosen_path / self.get_library_name()

    def get_library_name(self):
        return self.library_name_input.text().strip()

    def choose_directory(self):
        """Open a dialog to choose a directory and display the selected path."""
        directory = QFileDialog.getExistingDirectory(self, LABELS.SELECT_FOLDER)
        if directory:
            self.chosen_path = Path(directory)
            self.update_storage_label()

    def update_storage_label(self):
        if self.chosen_path:
            self.directory_label.setText(f"Metadata Storage Folder: {self.get_storage_path()}")
        else:
            self.directory_label.setText(LABELS.NO_FOLDER)
