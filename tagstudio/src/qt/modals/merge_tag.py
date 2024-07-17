from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QComboBox, QPushButton
from PySide6.QtCore import Qt

class MergeTagModal(QDialog):
    def __init__(self, library, current_tag):
        super().__init__()
        self.lib = library
        self.current_tag = current_tag
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        
        layout.addWidget(QLabel("Selected tag:"))
        self.selected_tag_dropdown = QComboBox(self)
        for tag in self.lib.tags:
            self.selected_tag_dropdown.addItem(tag.display_name(self.lib), tag)
        self.selected_tag_dropdown.setCurrentIndex(self.find_current_tag_index())
        layout.addWidget(self.selected_tag_dropdown)
        
        arrow_label = QLabel("↓")
        arrow_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(arrow_label)

        layout.addWidget(QLabel("Select tag to merge with:"))
        self.tag2_dropdown = QComboBox(self)
        for tag in self.lib.tags:
            if tag.id != self.current_tag.id:
                self.tag2_dropdown.addItem(tag.display_name(self.lib), tag)
        layout.addWidget(self.tag2_dropdown)

        self.merge_button = QPushButton("Merge", self)
        layout.addWidget(self.merge_button)

        self.merge_button.clicked.connect(self.merge_tags)

        self.setLayout(layout)

    def find_current_tag_index(self):
        for index in range(self.selected_tag_dropdown.count()):
            if self.selected_tag_dropdown.itemData(index) == self.current_tag:
                return index
        return 0

    def merge_tags(self):
        self.lib.merge_tag(self.current_tag, self.tag2_dropdown.currentData())
        self.accept()