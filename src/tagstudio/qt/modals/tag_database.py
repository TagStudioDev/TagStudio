# Copyright (C) 2024 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio


import structlog
from PySide6.QtWidgets import QMessageBox, QPushButton

from tagstudio.core.constants import RESERVED_TAG_END, RESERVED_TAG_START
from tagstudio.core.library.alchemy.library import Library
from tagstudio.core.library.alchemy.models import Tag
from tagstudio.qt.modals.build_tag import BuildTagPanel
from tagstudio.qt.modals.tag_search import TagSearchPanel
from tagstudio.qt.translations import Translations
from tagstudio.qt.widgets.panel import PanelModal

logger = structlog.get_logger(__name__)

# TODO: Once this class is removed, the `is_tag_chooser` option of `TagSearchPanel`
# will most likely be enabled in every case
# and the possibility of disabling it can therefore be removed


class TagDatabasePanel(TagSearchPanel):
    def __init__(self, driver, library: Library):
        super().__init__(library, is_tag_chooser=False)
        self.driver = driver

        self.create_tag_button = QPushButton(Translations["tag.create"])
        self.create_tag_button.clicked.connect(lambda: self.build_tag(self.search_field.text()))

        self.root_layout.addWidget(self.create_tag_button)

    def build_tag(self, name: str):
        panel = BuildTagPanel(self.lib)
        self.modal = PanelModal(
            panel,
            has_save=True,
        )
        self.modal.setTitle(Translations["tag.new"])
        self.modal.setWindowTitle(Translations["tag.new"])
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
                self.update_tags(self.search_field.text()),
            )
        )
        self.modal.show()

    def delete_tag(self, tag: Tag):
        if tag.id in range(RESERVED_TAG_START, RESERVED_TAG_END):
            return

        message_box = QMessageBox(
            QMessageBox.Question,  # type: ignore
            Translations["tag.remove"],
            Translations.format("tag.confirm_delete", tag_name=self.lib.tag_display_name(tag.id)),
            QMessageBox.Ok | QMessageBox.Cancel,  # type: ignore
        )

        result = message_box.exec()

        if result != QMessageBox.Ok:  # type: ignore
            return

        self.lib.remove_tag(tag)
        self.update_tags()
