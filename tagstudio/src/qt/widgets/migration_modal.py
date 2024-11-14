# Copyright (C) 2024 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)
from src.qt.helpers.qbutton_wrapper import QPushButtonWrapper
from src.qt.widgets.paged_panel.paged_body_wrapper import PagedBodyWrapper
from src.qt.widgets.paged_panel.paged_panel import PagedPanel
from src.qt.widgets.paged_panel.paged_panel_state import PagedPanelState


class MigrationModal:
    """A modal for data migration."""

    def __init__(self):
        self.stack: list[PagedPanelState] = []
        self.title: str = "Save Format Migration"
        self.warning: str = "<b><a style='color: #e22c3c'>(!)</a></b>"

        self.old_entry_count: int = 0
        self.old_tag_count: int = 0
        self.old_ext_count: int = 0

        self.init_page_00()
        self.init_page_01()

        self.paged_panel: PagedPanel = PagedPanel((640, 320), self.stack)

    def init_page_00(self) -> None:
        body_wrapper: PagedBodyWrapper = PagedBodyWrapper()
        body_label: QLabel = QLabel(
            "Library save files created with TagStudio versions <b>v9.4 and below</b> will "
            "need to be migrated to the new <b>v9.5+</b> format."
            "<br>"
            "<h2>What you need to know:</h2>"
            "<ul>"
            "<li>Your existing library save file will <b><i>NOT</i></b> be deleted</li>"
            "<li>Your personal files will <b><i>NOT</i></b> be deleted, moved, or modified</li>"
            "<li>The new v9.5+ save format can not be opened in earlier versions of TagStudio</li>"
            "</ul>"
        )
        body_label.setWordWrap(True)
        body_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        body_wrapper.layout().addWidget(body_label)

        cancel_button: QPushButtonWrapper = QPushButtonWrapper("Cancel")
        next_button: QPushButtonWrapper = QPushButtonWrapper("Next")

        self.stack.append(
            PagedPanelState(
                title=self.title,
                body_wrapper=body_wrapper,
                buttons=[cancel_button, 1, next_button],
                connect_to_back=[cancel_button],
                connect_to_next=[next_button],
            )
        )

    def init_page_01(self) -> None:
        body_wrapper: PagedBodyWrapper = PagedBodyWrapper()
        body_container: QWidget = QWidget()
        body_container_layout: QHBoxLayout = QHBoxLayout(body_container)
        body_container_layout.setContentsMargins(0, 0, 0, 0)

        entries_text: str = "Entries:"
        tags_text: str = "Tags:"
        ext_text: str = "File Extension List:"

        old_lib_container: QWidget = QWidget()
        old_lib_layout: QVBoxLayout = QVBoxLayout(old_lib_container)
        old_lib_title: QLabel = QLabel("<h2>v9.4 Library</h2>")
        old_lib_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        old_lib_layout.addWidget(old_lib_title)

        old_content_container: QWidget = QWidget()
        self.old_content_layout: QGridLayout = QGridLayout(old_content_container)
        self.old_content_layout.setContentsMargins(0, 0, 0, 0)
        self.old_content_layout.addWidget(QLabel(entries_text), 0, 0)
        self.old_content_layout.addWidget(QLabel(tags_text), 1, 0)
        self.old_content_layout.addWidget(QLabel(ext_text), 2, 0)

        old_entry_count: QLabel = QLabel()
        old_entry_count.setAlignment(Qt.AlignmentFlag.AlignRight)
        old_tag_count: QLabel = QLabel()
        old_tag_count.setAlignment(Qt.AlignmentFlag.AlignRight)
        old_ext_count: QLabel = QLabel()
        old_ext_count.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.old_content_layout.addWidget(old_entry_count, 0, 1)
        self.old_content_layout.addWidget(old_tag_count, 1, 1)
        self.old_content_layout.addWidget(old_ext_count, 2, 1)
        old_lib_layout.addWidget(old_content_container)

        new_lib_container: QWidget = QWidget()
        new_lib_layout: QVBoxLayout = QVBoxLayout(new_lib_container)
        new_lib_title: QLabel = QLabel("<h2>v9.5+ Library</h2>")
        new_lib_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        new_lib_layout.addWidget(new_lib_title)

        new_content_container: QWidget = QWidget()
        self.new_content_layout: QGridLayout = QGridLayout(new_content_container)
        self.new_content_layout.setContentsMargins(0, 0, 0, 0)
        self.new_content_layout.addWidget(QLabel(entries_text), 0, 0)
        self.new_content_layout.addWidget(QLabel(tags_text), 1, 0)
        self.new_content_layout.addWidget(QLabel(ext_text), 2, 0)

        self.new_content_layout.addWidget(QLabel(), 0, 2)
        self.new_content_layout.addWidget(QLabel(), 1, 2)
        self.new_content_layout.addWidget(QLabel(), 2, 2)

        new_entry_count: QLabel = QLabel()
        new_entry_count.setAlignment(Qt.AlignmentFlag.AlignRight)
        new_tag_count: QLabel = QLabel()
        new_tag_count.setAlignment(Qt.AlignmentFlag.AlignRight)
        new_ext_count: QLabel = QLabel()
        new_ext_count.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.new_content_layout.addWidget(new_entry_count, 0, 1)
        self.new_content_layout.addWidget(new_tag_count, 1, 1)
        self.new_content_layout.addWidget(new_ext_count, 2, 1)
        new_lib_layout.addWidget(new_content_container)

        self.update_values()

        body_container_layout.addStretch(2)
        body_container_layout.addWidget(old_lib_container)
        body_container_layout.addStretch(1)
        body_container_layout.addWidget(new_lib_container)
        body_container_layout.addStretch(2)

        body_wrapper.layout().addWidget(body_container)

        back_button: QPushButtonWrapper = QPushButtonWrapper("Back")
        finish_button: QPushButtonWrapper = QPushButtonWrapper("Finish Migration")

        self.stack.append(
            PagedPanelState(
                title=self.title,
                body_wrapper=body_wrapper,
                buttons=[back_button, 1, finish_button],
                connect_to_back=[back_button],
                connect_to_next=[finish_button],
            )
        )

    def update_values(self):
        self.update_old_entry_count(0)
        self.update_old_tag_count(10)
        self.update_old_ext_count(2000)
        self.update_new_entry_count(0)
        self.update_new_tag_count(100000)
        self.update_new_ext_count(2000)

    def update_old_entry_count(self, value: int):
        self.old_entry_count = value
        label: QLabel = self.old_content_layout.itemAtPosition(0, 1).widget()  # type:ignore
        label.setText(self.color_value_default(value))

    def update_old_tag_count(self, value: int):
        self.old_tag_count = value
        label: QLabel = self.old_content_layout.itemAtPosition(1, 1).widget()  # type:ignore
        label.setText(self.color_value_default(value))

    def update_old_ext_count(self, value: int):
        self.old_ext_count = value
        label: QLabel = self.old_content_layout.itemAtPosition(2, 1).widget()  # type:ignore
        label.setText(self.color_value_default(value))

    def update_new_entry_count(self, value: int):
        label: QLabel = self.new_content_layout.itemAtPosition(0, 1).widget()  # type:ignore
        warning_icon: QLabel = self.new_content_layout.itemAtPosition(0, 2).widget()  # type:ignore
        label.setText(self.color_value_conditional(self.old_entry_count, value))
        warning_icon.setText("" if self.old_entry_count == value else self.warning)

    def update_new_tag_count(self, value: int):
        label: QLabel = self.new_content_layout.itemAtPosition(1, 1).widget()  # type:ignore
        warning_icon: QLabel = self.new_content_layout.itemAtPosition(1, 2).widget()  # type:ignore
        label.setText(self.color_value_conditional(self.old_tag_count, value))
        warning_icon.setText("" if self.old_tag_count == value else self.warning)

    def update_new_ext_count(self, value: int):
        label: QLabel = self.new_content_layout.itemAtPosition(2, 1).widget()  # type:ignore
        warning_icon: QLabel = self.new_content_layout.itemAtPosition(2, 2).widget()  # type:ignore
        label.setText(self.color_value_conditional(self.old_ext_count, value))
        warning_icon.setText("" if self.old_ext_count == value else self.warning)

    def color_value_default(self, value: int) -> str:
        """Apply the default color to a value."""
        return str(f"<b><a style='color: #3b87f0'>{value}</a></b>")

    def color_value_conditional(self, old_value: int, new_value: int) -> str:
        """Apply the default color to a value."""
        red: str = "#e22c3c"
        green: str = "#28bb48"
        color = green if old_value == new_value else red
        return str(f"<b><a style='color: {color}'>{new_value}</a></b>")
