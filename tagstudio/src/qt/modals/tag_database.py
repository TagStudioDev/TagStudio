# Copyright (C) 2024 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio

import structlog
from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QShowEvent
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)
from src.core.constants import RESERVED_TAG_IDS
from src.core.library import Library, Tag
from src.qt.modals.build_tag import BuildTagPanel
from src.qt.widgets.panel import PanelModal, PanelWidget
from src.qt.widgets.tag import TagWidget

logger = structlog.get_logger(__name__)

# TODO: This class shares the majority of its code with tag_search.py.
# It should either be made DRY, or be replaced with the intended and more robust
# Tag Management tab/pane outlined on the Feature Roadmap.


class TagDatabasePanel(PanelWidget):
    tag_chosen = Signal(int)

    def __init__(self, library: Library):
        super().__init__()
        self.lib: Library = library
        self.is_initialized: bool = False
        self.first_tag_id = -1

        self.setMinimumSize(300, 400)
        self.root_layout = QVBoxLayout(self)
        self.root_layout.setContentsMargins(6, 0, 6, 0)

        self.search_field = QLineEdit()
        self.search_field.setObjectName("searchField")
        self.search_field.setMinimumSize(QSize(0, 32))
        self.search_field.setPlaceholderText("Search Tags")
        self.search_field.textEdited.connect(lambda: self.update_tags(self.search_field.text()))
        self.search_field.returnPressed.connect(
            lambda checked=False: self.on_return(self.search_field.text())
        )

        self.scroll_contents = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_contents)
        self.scroll_layout.setContentsMargins(6, 0, 6, 0)
        self.scroll_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.scroll_area = QScrollArea()
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShadow(QFrame.Shadow.Plain)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_area.setWidget(self.scroll_contents)

        self.create_tag_button = QPushButton()
        self.create_tag_button.setText("Create Tag")
        self.create_tag_button.clicked.connect(self.build_tag)

        self.root_layout.addWidget(self.search_field)
        self.root_layout.addWidget(self.scroll_area)
        self.root_layout.addWidget(self.create_tag_button)
        self.update_tags()

    def build_tag(self):
        self.modal = PanelModal(
            BuildTagPanel(self.lib),
            "New Tag",
            "Add Tag",
            has_save=True,
        )

        panel: BuildTagPanel = self.modal.widget
        self.modal.saved.connect(
            lambda: (
                self.lib.add_tag(panel.build_tag(), panel.subtag_ids),
                self.modal.hide(),
                self.update_tags(),
            )
        )
        self.modal.show()

    def on_return(self, text: str):
        if text and self.first_tag_id >= 0:
            # callback(self.first_tag_id)
            self.search_field.setText("")
            self.update_tags()
        else:
            self.search_field.setFocus()
            self.parentWidget().hide()

    def update_tags(self, query: str | None = None):
        # TODO: Look at recycling rather than deleting and re-initializing
        logger.info("[Tag Manager Modal] Updating Tags")
        while self.scroll_layout.itemAt(0):
            self.scroll_layout.takeAt(0).widget().deleteLater()

        tags_results = self.lib.search_tags(name=query)

        for tag in tags_results:
            container = QWidget()
            row = QHBoxLayout(container)
            row.setContentsMargins(0, 0, 0, 0)
            row.setSpacing(3)

            if tag.id in RESERVED_TAG_IDS:
                tag_widget = TagWidget(tag, has_edit=False, has_remove=False)
            else:
                tag_widget = TagWidget(tag, has_edit=True, has_remove=True)

            tag_widget.on_edit.connect(lambda checked=False, t=tag: self.edit_tag(t))
            tag_widget.on_remove.connect(lambda t=tag: self.remove_tag(t))
            row.addWidget(tag_widget)
            self.scroll_layout.addWidget(container)

        self.search_field.setFocus()

    def remove_tag(self, tag: Tag):
        if tag.id in RESERVED_TAG_IDS:
            return

        message_box = QMessageBox()
        message_box.setWindowTitle("Remove tag")
        message_box.setText("Are you sure you want to remove " + tag.name + "?")
        message_box.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)  # type: ignore
        message_box.setIcon(QMessageBox.Question)  # type: ignore

        result = message_box.exec()

        if result != QMessageBox.Ok:  # type: ignore
            return

        self.lib.remove_tag(tag)
        self.update_tags()

    def edit_tag(self, tag: Tag):
        if tag.id in RESERVED_TAG_IDS:
            return

        build_tag_panel = BuildTagPanel(self.lib, tag=tag)

        self.edit_modal = PanelModal(
            build_tag_panel,
            tag.name,
            "Edit Tag",
            done_callback=(self.update_tags(self.search_field.text())),
            has_save=True,
        )
        # TODO Check Warning: Expected type 'BuildTagPanel', got 'PanelWidget' instead
        self.edit_modal.saved.connect(lambda: self.edit_tag_callback(build_tag_panel))
        self.edit_modal.show()

    def edit_tag_callback(self, btp: BuildTagPanel):
        self.lib.update_tag(btp.build_tag(), btp.subtag_ids, btp.alias_names, btp.alias_ids)
        self.update_tags(self.search_field.text())

    def showEvent(self, event: QShowEvent) -> None:  # noqa N802
        if not self.is_initialized:
            self.update_tags()
            self.is_initialized = True
        return super().showEvent(event)
