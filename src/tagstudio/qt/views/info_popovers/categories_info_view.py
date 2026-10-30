# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from tagstudio.core.library.alchemy import default_color_groups
from tagstudio.i18n.translations import Translations
from tagstudio.qt.controllers.badge import Badge
from tagstudio.qt.controllers.capsule import Capsule
from tagstudio.qt.controllers.inset_frame import InsetFrame
from tagstudio.qt.resource_manager import ResourceManager
from tagstudio.qt.views.info_popovers.info_popover_view import InfoPopoverView
from tagstudio.qt.views.styles.stylesheets import HALF_PAD, PAD, inset_container_style


class CategoriesInfoView(InfoPopoverView):
    """An info popover example for explaining tag categories and category visibility."""

    def __init__(self) -> None:
        super().__init__()
        food = Translations["tag.info.example.food"]
        fruit = Translations["tag.info.example.fruit"]
        banana = Translations["tag.info.example.banana"]
        category_note = Translations["tag.is_category"] + " <b>✓</b>"
        # TODO: Add a better way to get tag colors
        yellow = next(c for c in default_color_groups.standard() if c.slug == "yellow")

        # Hierarchy Visual
        hierarchy = self._example_tree(
            [self._example_capsule(food), self._dim_label(category_note)],
            [self._example_capsule(fruit), self._dim_label(category_note)],
            [self._example_capsule(banana, yellow)],
        )
        grouped = self._example_inspector(
            (food, self._example_capsule(banana, yellow)),
            (fruit, self._example_capsule(banana, yellow)),
        )

        # Category Visibility Visual
        visibility = self._example(
            self._example_row(self._example_badge(checked=False), self._example_capsule(food)),
            self._example_row(self._example_badge(checked=True), self._example_capsule(fruit)),
        )
        visible = self._example_inspector((fruit, self._example_capsule(banana, yellow)))

        # Finalize Layout
        self._add_section(
            Translations["tag.categories"],
            Translations["tag.categories.info.description"],
            header_level=3,
        )
        self._add_section(
            Translations["tag.categories.info.setup.title"],
            Translations.format(
                "tag.categories.info.setup.description",
                is_category=Translations["tag.is_category"],
            ),
        )
        self.addWidget(self._example_result(hierarchy, grouped))
        self._add_section(
            Translations["tag.categories.info.visibility.title"],
            Translations.format(
                "tag.categories.info.visibility.description", child=banana, parent=food
            ),
        )
        self.addWidget(self._example_result(visibility, visible))

    def _example_inspector(self, *sections: tuple[str, Capsule]) -> QWidget:
        """A mock Inspector tile showing each category heading with its tag(s)."""
        frame = InsetFrame()
        frame.setObjectName("example_inspector")
        frame.setStyleSheet(inset_container_style("example_inspector"))
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(PAD, PAD, PAD, PAD)
        layout.setSpacing(PAD)
        for title, capsule in sections:
            section = QWidget()
            section_layout = QVBoxLayout(section)
            section_layout.setContentsMargins(0, 0, 0, 0)
            section_layout.setSpacing(HALF_PAD)
            section_layout.addWidget(QLabel(f"<b>{title}</b>"))
            section_layout.addWidget(self._example_row(capsule))
            layout.addWidget(section)
        return self._example(frame)

    def _example_badge(self, checked: bool) -> Badge:
        badge = Badge(
            ResourceManager().eye, is_circular=False, unchecked_icon=ResourceManager().eye_closed
        )
        badge.setChecked(checked)
        badge.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        return badge
