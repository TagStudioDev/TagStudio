# Copyright (C) 2024 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio

import structlog
from PySide6.QtWidgets import (
    QMessageBox,
    QPushButton,
)
from src.core.constants import RESERVED_TAG_END, RESERVED_TAG_START
from src.core.library import Library, Tag
from src.qt.modals.build_tag import BuildTagPanel
from src.qt.modals.tag_search import TagSearchPanel
from src.qt.translations import Translations
from src.qt.widgets.panel import PanelModal

logger = structlog.get_logger(__name__)

# TODO: Once this class is removed, the `is_tag_chooser` option of `TagSearchPanel`
# will most likely be enabled in every case
# and the possibilty of disabling it can therefore be removed


class TagDatabasePanel(TagSearchPanel):
    def __init__(self, library: Library):
        super().__init__(library, is_tag_chooser=False)

        self.create_tag_button = QPushButton()
        Translations.translate_qobject(self.create_tag_button, "tag.create")
        self.create_tag_button.clicked.connect(lambda: self.build_tag(self.search_field.text()))

        self.root_layout.addWidget(self.create_tag_button)
        self.update_tags()

    def build_tag(self, name: str):
        panel = BuildTagPanel(self.lib)
        self.modal = PanelModal(
            panel,
            has_save=True,
        )
        Translations.translate_with_setter(self.modal.setTitle, "tag.new")
        Translations.translate_with_setter(self.modal.setWindowTitle, "tag.add")
        if name.strip():
            panel.name_field.setText(name)

        self.modal.saved.connect(
            lambda: (
                self.lib.add_tag(
                    tag=panel.build_tag(),
                    parent_ids=panel.parent_ids,
                    alias_names=panel.alias_names,
                    alias_ids=panel.alias_ids,
                ),
                self.modal.hide(),
                self.update_tags(),
            )
        )
        self.modal.show()

    def remove_tag(self, tag: Tag):
        if tag.id in range(RESERVED_TAG_START, RESERVED_TAG_END):
            return

        message_box = QMessageBox()
        Translations.translate_with_setter(message_box.setWindowTitle, "tag.remove")
        Translations.translate_qobject(
            message_box, "tag.confirm_delete", tag_name=self.lib.tag_display_name(tag.id)
        )
        message_box.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)  # type: ignore
        message_box.setIcon(QMessageBox.Question)  # type: ignore

        result = message_box.exec()

        if result != QMessageBox.Ok:  # type: ignore
            return

        self.lib.remove_tag(tag)
        self.update_tags()
