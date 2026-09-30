# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QFrame,
    QGraphicsOpacityEffect,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QTableWidget,
    QVBoxLayout,
    QWidget,
)

from tagstudio.i18n.translations import Translations
from tagstudio.qt.controllers.capsule import Capsule
from tagstudio.qt.views.styles.stylesheets import checkbox_style, header


class EditTagPanelView(QVBoxLayout):
    def __init__(self) -> None:
        super().__init__()
        self.setContentsMargins(6, 0, 6, 0)
        self.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Name -----------------------------------------------------------------
        name_widget = QWidget()
        name_layout = QVBoxLayout(name_widget)
        name_layout.setContentsMargins(0, 0, 0, 0)
        name_layout.setSpacing(0)
        name_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        name_layout.addWidget(QLabel(Translations["tag.name"]))
        self.name_field = QLineEdit()
        self.name_field.setFixedHeight(24)
        self.name_field.setPlaceholderText(Translations["tag.tag_name_required"])
        name_layout.addWidget(self.name_field)

        # Shorthand ------------------------------------------------------------
        shorthand_widget = QWidget()
        shorthand_layout = QVBoxLayout(shorthand_widget)
        shorthand_layout.setContentsMargins(0, 0, 0, 0)
        shorthand_layout.setSpacing(0)
        shorthand_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        shorthand_layout.addWidget(QLabel(Translations["tag.shorthand"]))
        self.shorthand_field = QLineEdit()
        shorthand_layout.addWidget(self.shorthand_field)

        # Aliases --------------------------------------------------------------
        aliases_title = QLabel(Translations["tag.aliases"])

        self.aliases_table = QTableWidget(0, 2)
        self.aliases_table.horizontalHeader().setVisible(False)
        self.aliases_table.verticalHeader().setVisible(False)
        self.aliases_table.horizontalHeader().setStretchLastSection(True)
        self.aliases_table.setColumnWidth(0, 32)
        self.aliases_table.setTabKeyNavigation(False)
        self.aliases_table.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        self.aliases_add_button = QPushButton("+")

        # Parent Tags ----------------------------------------------------------
        parent_tags_widget = QWidget()
        parent_tags_layout = QVBoxLayout(parent_tags_widget)
        parent_tags_layout.setContentsMargins(0, 0, 0, 0)
        parent_tags_layout.setSpacing(0)
        parent_tags_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        parent_tags_layout.addWidget(QLabel(header(Translations["tag.parent_tags"], 3)))

        parent_tags_scroll_contents = QWidget()
        self.parent_tags_scroll_layout = QVBoxLayout(parent_tags_scroll_contents)
        self.parent_tags_scroll_layout.setContentsMargins(6, 6, 6, 0)
        self.parent_tags_scroll_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        parent_tags_layout.addWidget(self._scroll_area(parent_tags_scroll_contents))

        self.parent_tags_add_button = QPushButton("+")
        self.parent_tags_add_button.setCursor(Qt.CursorShape.PointingHandCursor)
        parent_tags_layout.addWidget(self.parent_tags_add_button)

        # Categories -----------------------------------------------------------
        category_widget = QWidget()
        category_layout = QVBoxLayout(category_widget)
        category_layout.setContentsMargins(0, 0, 0, 0)
        category_layout.setSpacing(0)
        category_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        category_layout.addWidget(QLabel(header(Translations["tag.categories"], 3)))

        category_subtitle = QLabel(Translations["tag.categories.subtitle"])
        opacity_effect = QGraphicsOpacityEffect(category_subtitle)
        opacity_effect.setOpacity(0.5)
        category_subtitle.setGraphicsEffect(opacity_effect)
        category_layout.addWidget(category_subtitle)

        category_scroll_contents = QWidget()
        self.category_scroll_layout = QVBoxLayout(category_scroll_contents)
        self.category_scroll_layout.setContentsMargins(6, 6, 6, 0)
        self.category_scroll_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        category_layout.addWidget(self._scroll_area(category_scroll_contents))

        # Color ----------------------------------------------------------------
        color_widget = QWidget()
        color_layout = QVBoxLayout(color_widget)
        color_layout.setContentsMargins(0, 0, 0, 6)
        color_layout.setSpacing(6)
        color_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        color_layout.addWidget(QLabel(header(Translations["tag.color"], 3)))
        self.color_button = Capsule(padded=True)
        color_layout.addWidget(self.color_button)

        # Properties -----------------------------------------------------------
        self.is_category_checkbox = QCheckBox()
        is_category_widget = self._checkbox_row(
            self.is_category_checkbox, Translations["tag.is_category"]
        )
        self.is_hidden_checkbox = QCheckBox()
        is_hidden_widget = self._checkbox_row(
            self.is_hidden_checkbox, Translations["tag.is_hidden"]
        )

        # Add Widgets to Layout ================================================
        self.addWidget(name_widget)
        self.addWidget(shorthand_widget)
        self.addWidget(aliases_title)
        self.addWidget(self.aliases_table, stretch=1)
        self.addWidget(self.aliases_add_button)
        self._add_spaced_separator()
        self.addWidget(parent_tags_widget, stretch=1)
        self._add_spaced_separator()
        self.addWidget(category_widget)
        self._add_spaced_separator()
        self.addWidget(color_widget)
        self._add_spaced_separator()
        self.addWidget(QLabel(header(Translations["tag.properties"], 3)))
        self.addWidget(is_category_widget)
        self.addWidget(is_hidden_widget)

    def _scroll_area(self, contents: QWidget) -> QScrollArea:
        scroll_area = QScrollArea()
        scroll_area.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShadow(QFrame.Shadow.Plain)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        scroll_area.setWidget(contents)
        return scroll_area

    def _checkbox_row(self, checkbox: QCheckBox, title: str) -> QWidget:
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        checkbox.setFixedSize(22, 22)
        checkbox.setStyleSheet(checkbox_style())
        layout.addWidget(checkbox)
        layout.addWidget(QLabel(title))
        return widget

    def _add_spaced_separator(self) -> None:
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setFrameShadow(QFrame.Shadow.Plain)
        opacity_effect = QGraphicsOpacityEffect(sep)
        opacity_effect.setOpacity(0.1)
        sep.setGraphicsEffect(opacity_effect)

        self.addSpacing(6)
        self.addWidget(sep)
        self.addSpacing(6)
