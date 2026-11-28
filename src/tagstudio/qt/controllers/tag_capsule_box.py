# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


from collections.abc import Callable

from PySide6.QtCore import Signal

from tagstudio.core.library.alchemy.library import Library
from tagstudio.core.library.tag_cache import CachedTag
from tagstudio.i18n.translations import Translations
from tagstudio.qt.controllers.capsule import Capsule
from tagstudio.qt.controllers.capsule_box import CapsuleBox
from tagstudio.qt.entry_state import EntryState
from tagstudio.qt.pinned_tags_state import PinnedTagsState
from tagstudio.qt.views.styles.stylesheets import PAD, TagShape
from tagstudio.qt.views.styles.tag_icons import tag_icon


class TagCapsuleBox(CapsuleBox):
    """Tag capsules in a flow layout inside a scrolling inset frame."""

    tag_chosen = Signal(int)
    edit_tag_requested = Signal(int)
    search_for_tag = Signal(int)

    def __init__(
        self,
        library: Library,
        entry_state: EntryState,
        pinned_tags_state: PinnedTagsState,
        sort_key: Callable[[CachedTag], str] | None = None,
    ) -> None:
        super().__init__()
        self._lib = library
        self._pinned_tags_state = pinned_tags_state
        self._sort_key = sort_key
        self._tag_ids: list[int] = []
        entry_state.tags_edited.connect(self._on_tags_edited)
        self.restyle()

    @property
    def tag_ids(self) -> list[int]:
        return self._tag_ids

    def set_tag_ids(self, tag_ids: list[int]) -> None:
        """Show capsules for these tags, leaving out tags that don't exist."""
        cached_tags = (self._lib.get_cached_tag(tag_id) for tag_id in tag_ids)
        tags = [tag for tag in cached_tags if tag is not None]
        if self._sort_key is not None:
            tags.sort(key=self._sort_key)
        self._tag_ids = [tag.id for tag in tags]
        capsules: list[Capsule] = []
        for tag in tags:
            capsule = Capsule(
                has_edit=True,
                has_pin=True,
                search_label=Translations["tag.search_for_tag"],
                is_tag=True,
            )
            capsule.set_text(self._lib.tag_display_name(tag))
            capsule.set_color_group(tag.color)
            capsule.set_icon(tag_icon(tag.id))
            capsule.on_click.connect(lambda tag_id=tag.id: self.tag_chosen.emit(tag_id))
            capsule.on_context_menu.connect(
                lambda capsule=capsule, tag_id=tag.id: capsule.set_pinned(
                    self._pinned_tags_state.is_pinned(tag_id)
                )
            )
            capsule.on_edit.connect(lambda tag_id=tag.id: self.edit_tag_requested.emit(tag_id))
            capsule.on_pin.connect(
                lambda is_pinned, tag_id=tag.id: self._pinned_tags_state.set_pinned(
                    tag_id, is_pinned
                )
            )
            capsule.on_search.connect(lambda tag_id=tag.id: self.search_for_tag.emit(tag_id))
            capsules.append(capsule)
        self.set_capsules(capsules)

    def restyle(self) -> None:
        """Style the capsules' inset to match the tag shape."""
        self.layout().scroll_box.set_content_inset(TagShape.content_inset(PAD))

    def _on_tags_edited(self, tag_ids: set[int]) -> None:  # pyright: ignore[reportUnusedParameter]
        """Show the tags again after any are edited or deleted."""
        self.set_tag_ids(self._tag_ids)
