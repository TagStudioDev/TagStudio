# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


from PySide6.QtCore import Signal

from tagstudio.core.library.alchemy.library import Library
from tagstudio.i18n.translations import Translations
from tagstudio.qt.controllers.capsule import Capsule
from tagstudio.qt.controllers.capsule_box import CapsuleBox
from tagstudio.qt.entry_state import EntryState
from tagstudio.qt.views.styles.stylesheets import PAD, TagShape
from tagstudio.qt.views.styles.tag_icons import tag_icon


class TagCapsuleBox(CapsuleBox):
    """Tag capsules in a flow layout inside a scrolling inset frame."""

    tag_chosen = Signal(int)
    edit_tag_requested = Signal(int)
    search_for_tag = Signal(int)

    def __init__(self, library: Library, entry_state: EntryState) -> None:
        super().__init__()
        self._lib = library
        self._tag_ids: list[int] = []
        entry_state.tags_edited.connect(self._on_tags_edited)
        self.restyle()

    @property
    def tag_ids(self) -> list[int]:
        return self._tag_ids

    def set_tag_ids(self, tag_ids: list[int]) -> None:
        """Show capsules for these tags, leaving out tags that don't exist."""
        self._tag_ids = []
        capsules: list[Capsule] = []
        for tag_id in tag_ids:
            tag = self._lib.get_cached_tag(tag_id)
            if tag is None:
                continue
            capsule = Capsule(
                has_edit=True, search_label=Translations["tag.search_for_tag"], is_tag=True
            )
            capsule.set_text(self._lib.tag_display_name(tag))
            capsule.set_color_group(tag.color)
            capsule.set_icon(tag_icon(tag_id))
            capsule.on_click.connect(lambda tag_id=tag_id: self.tag_chosen.emit(tag_id))
            capsule.on_edit.connect(lambda tag_id=tag_id: self.edit_tag_requested.emit(tag_id))
            capsule.on_search.connect(lambda tag_id=tag_id: self.search_for_tag.emit(tag_id))
            capsules.append(capsule)
            self._tag_ids.append(tag_id)
        self.set_capsules(capsules)

    def restyle(self) -> None:
        """Style the capsules' inset to match the tag shape."""
        self.layout().scroll_box.set_content_inset(TagShape.content_inset(PAD))

    def _on_tags_edited(self, tag_ids: set[int]) -> None:  # pyright: ignore[reportUnusedParameter]
        """Show the tags again after any are edited or deleted."""
        self.set_tag_ids(self._tag_ids)
