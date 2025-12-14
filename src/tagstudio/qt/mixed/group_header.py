# Copyright (C) 2025 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio


from typing import TYPE_CHECKING, Any, override

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QWidget

from tagstudio.core.library.alchemy.models import Tag
from tagstudio.qt.mixed.tag_widget import TagWidget

# Only import for type checking/autocompletion, will not be imported at runtime.
if TYPE_CHECKING:
    from tagstudio.core.library.alchemy.grouping import EntryGroup
    from tagstudio.core.library.alchemy.library import Library


class GroupHeaderWidget(QWidget):
    """Collapsible header widget for entry groups."""

    toggle_collapsed = Signal()

    def __init__(
        self,
        tag: Tag | None,
        entry_count: int,
        is_collapsed: bool = False,
        is_special: bool = False,
        special_label: str | None = None,
        library: "Library | None" = None,
        is_first: bool = False,
        tags: list[Tag] | None = None,
        key: Any | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Initialize the group header widget.

        Args:
            tag: The tag for this group (None for non-tag groups) - deprecated, use key.
            entry_count: Number of entries in this group.
            is_collapsed: Whether the group starts collapsed.
            is_special: Whether this is a special group.
            special_label: Label for special groups.
            library: Library instance for tag operations.
            is_first: Whether this is the first group (no divider needed).
            tags: Multiple tags for multi-tag combination groups - deprecated.
            key: Generic key for the group (replaces tag).
            metadata: Additional metadata for the group.
        """
        super().__init__()
        self.key = key if key is not None else tag
        self.tag = tag
        self.entry_count = entry_count
        self.is_collapsed = is_collapsed
        self.is_special = is_special
        self.special_label = special_label
        self.lib = library
        self.tags = tags
        self.metadata = metadata or {}

        self.setCursor(Qt.CursorShape.PointingHandCursor)

        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(6, 4, 6, 4)
        self.main_layout.setSpacing(8)

        self.arrow_button = QPushButton(self)
        self.arrow_button.setFlat(True)
        self.arrow_button.setFixedSize(20, 20)
        self.arrow_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.arrow_button.setStyleSheet(
            "QPushButton { border: none; text-align: center; font-size: 12px; padding: 0px; }"
        )
        self._update_arrow()
        self.arrow_button.clicked.connect(self._on_toggle)
        self.main_layout.addWidget(self.arrow_button)

        if tags:
            self.tags_container = QWidget(self)
            self.tags_layout = QHBoxLayout(self.tags_container)
            self.tags_layout.setContentsMargins(0, 0, 0, 0)
            self.tags_layout.setSpacing(4)

            for tag_obj in tags:
                tag_widget = TagWidget(
                    tag=tag_obj, has_edit=False, has_remove=False, library=library
                )
                self.tags_layout.addWidget(tag_widget)

            self.main_layout.addWidget(self.tags_container)
        elif is_special and special_label:
            self.label = QLabel(special_label, self)
            self.label.setStyleSheet(
                "font-weight: bold; "
                "font-size: 12px; "
                "padding: 2px 8px; "
                "border-radius: 4px; "
                "background-color: #3a3a3a; "
                "color: #e0e0e0;"
            )
            self.main_layout.addWidget(self.label)
        elif tag or isinstance(self.key, Tag):
            self.tag_widget = TagWidget(tag=tag, has_edit=False, has_remove=False, library=library)
            self.main_layout.addWidget(self.tag_widget)
        elif self.key is not None:
            # Generic group with non-tag key (e.g., filetype)
            self.label = QLabel(str(self.key), self)
            self.label.setStyleSheet(
                "font-weight: bold; "
                "font-size: 12px; "
                "padding: 2px 8px; "
                "border-radius: 4px; "
                "background-color: #3a3a3a; "
                "color: #e0e0e0;"
            )
            self.main_layout.addWidget(self.label)

        count_text = f"({entry_count} {'entry' if entry_count == 1 else 'entries'})"
        self.count_label = QLabel(count_text, self)
        self.count_label.setStyleSheet("color: #888888; font-size: 11px;")
        self.main_layout.addWidget(self.count_label)

        self.main_layout.addStretch(1)

        if is_first:
            divider_style = ""
        else:
            divider_style = "margin-top: 8px; border-top: 1px solid #444444; padding-top: 4px; "

        self.setStyleSheet(
            "GroupHeaderWidget { "
            "background-color: #2a2a2a; "
            f"{divider_style}"
            "} "
            "GroupHeaderWidget:hover { "
            "background-color: #333333; "
            "}"
        )

        self.setMinimumHeight(32)
        self.setMaximumHeight(32)

    @classmethod
    def from_group(
        cls,
        group: "EntryGroup",
        is_collapsed: bool = False,
        library: "Library | None" = None,
        is_first: bool = False,
    ) -> "GroupHeaderWidget":
        """Create a GroupHeaderWidget from an EntryGroup.

        Args:
            group: The entry group to create a header for.
            is_collapsed: Whether the group starts collapsed.
            library: Library instance for tag operations.
            is_first: Whether this is the first group (no divider needed).

        Returns:
            GroupHeaderWidget instance.
        """
        # Extract tag if key is a Tag
        tag = group.key if isinstance(group.key, Tag) else None

        return cls(
            tag=tag,
            entry_count=len(group.entry_ids),
            is_collapsed=is_collapsed,
            is_special=group.is_special,
            special_label=group.special_label,
            library=library,
            is_first=is_first,
            key=group.key,
            metadata=group.metadata,
        )

    def _update_arrow(self) -> None:
        """Update the arrow button to show collapsed or expanded state."""
        if self.is_collapsed:
            self.arrow_button.setText("▶")  # Collapsed (pointing right)
        else:
            self.arrow_button.setText("▼")  # Expanded (pointing down)

    def _on_toggle(self) -> None:
        """Handle toggle button click."""
        self.is_collapsed = not self.is_collapsed
        self._update_arrow()
        self.toggle_collapsed.emit()

    @override
    def mousePressEvent(self, event) -> None:
        """Handle mouse press on the entire widget (not just arrow)."""
        if event.button() == Qt.MouseButton.LeftButton:
            self._on_toggle()
        super().mousePressEvent(event)
