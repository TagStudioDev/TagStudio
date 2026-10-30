# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget

from tagstudio.core.library.alchemy import default_color_groups
from tagstudio.i18n.translations import Translations
from tagstudio.qt.controllers.badge import Badge
from tagstudio.qt.resource_manager import ResourceManager
from tagstudio.qt.views.info_popovers.info_popover_view import InfoPopoverView


class ParentTagsInfoView(InfoPopoverView):
    """An info popover example for explaining parent tags and name disambiguation."""

    def __init__(self) -> None:
        super().__init__()
        food = Translations["tag.info.example.food"]
        fruit = Translations["tag.info.example.fruit"]
        banana = Translations["tag.info.example.banana"]
        king = Translations["tag.info.example.king"]
        # TODO: Add a better way to get tag colors
        yellow = next(c for c in default_color_groups.standard() if c.slug == "yellow")

        # Hierarchy Visual
        hierarchy = self._example_tree(
            [self._example_capsule(food)],
            [
                self._example_capsule(fruit),
                self._dim_label(Translations.format("tag.parent_tags.info.is_a", parent=food)),
            ],
            [
                self._example_capsule(banana, yellow),
                self._dim_label(
                    Translations.format(
                        "tag.parent_tags.info.is_a_both", parent=fruit, grandparent=food
                    )
                ),
            ],
        )

        # Disambiguation Visual
        disambiguation_rows: list[QWidget] = []
        for parent in (
            Translations["tag.info.example.chess_piece"],
            Translations["tag.info.example.playing_card"],
        ):
            capsule = self._example_capsule(parent, min_width=120)
            arrow = self._icon_label(ResourceManager().arrow_right)
            # Keep rows as tall as their tags so the gaps between rows match the layout spacing
            arrow.setFixedHeight(capsule.sizeHint().height())
            disambiguation_rows.append(
                self._example_row(
                    self._example_badge(),
                    capsule,
                    arrow,
                    self._example_capsule(f"{king} ({parent})"),
                )
            )
        searches = Translations.format(
            "tag.parent_tags.info.searches.description",
            child=banana,
            parent=fruit,
            grandparent=food,
        )

        # Finalize Layout
        self._add_section(
            Translations["tag.parent_tags"],
            Translations["tag.parent_tags.info.description"],
            header_level=3,
        )
        self.addWidget(hierarchy)
        self._add_section(Translations["tag.parent_tags.info.searches.title"], searches)
        self._add_section(
            Translations["tag.parent_tags.info.disambiguation.title"],
            Translations.format("tag.parent_tags.info.disambiguation.description", name=king),
        )
        self.addWidget(self._example(*disambiguation_rows))

    def _example_badge(self) -> Badge:
        badge = Badge(ResourceManager().card_text, is_circular=True)
        badge.setChecked(True)
        badge.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        return badge
