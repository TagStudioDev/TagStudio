# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QAction, QTransform
from PySide6.QtWidgets import (
    QGraphicsOpacityEffect,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from tagstudio.i18n.platform_strings import open_file_str
from tagstudio.i18n.translations import Translations
from tagstudio.qt.controllers.file_opener_label import FileOpenerLabel
from tagstudio.qt.resource_manager import ResourceManager
from tagstudio.qt.views.styles.color_overlay import svg_color_overlay, theme_foreground_color
from tagstudio.qt.views.styles.palette import UiColor
from tagstudio.qt.views.styles.stylesheets import (
    HALF_PAD,
    PAD,
    boxed_label_style,
    icon_button_style,
)

_TOGGLE_ICON_SIZE = 18
_NAME_FONT_PIXEL_SIZE = 12
_DETAILS_FONT_PIXEL_SIZE = 11


class FileAttributesView(QVBoxLayout):
    """The layout for a selected file's name, folder path, and properties."""

    def __init__(self) -> None:
        super().__init__()
        self.setContentsMargins(0, 0, 0, 0)
        self.setSpacing(0)

        self.open_file_action = QAction(Translations["file.open_file"], self)
        self.open_explorer_action = QAction(open_file_str(), self)
        self.copy_filename_action = QAction(Translations["file.copy_filename"], self)
        self.copy_path_action = QAction(Translations["file.copy_path"], self)

        self.message_label = QLabel()
        self.message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.addWidget(self.message_label)

        self.header = QWidget()
        header_layout = QHBoxLayout(self.header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(HALF_PAD)
        self.ignored_label = self._boxed_label("preview.ignored", UiColor.ORANGE)
        header_layout.addWidget(self.ignored_label, alignment=Qt.AlignmentFlag.AlignVCenter)
        self.unlinked_label = self._boxed_label("preview.unlinked", UiColor.RED)
        header_layout.addWidget(self.unlinked_label, alignment=Qt.AlignmentFlag.AlignVCenter)
        self.ext_label = QLabel()
        self.ext_label.setStyleSheet(boxed_label_style())
        header_layout.addWidget(self.ext_label, alignment=Qt.AlignmentFlag.AlignVCenter)
        self.name_label = FileOpenerLabel()
        self._set_pixel_size(self.name_label, _NAME_FONT_PIXEL_SIZE)
        self._add_file_actions(self.name_label)
        header_layout.addWidget(self.name_label, stretch=1)
        self.toggle_button = QPushButton()
        self.toggle_button.setFlat(True)
        self.toggle_button.setStyleSheet(icon_button_style())
        self.toggle_button.setFixedWidth(_TOGGLE_ICON_SIZE)
        self.toggle_button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Ignored)
        self.toggle_button.setIconSize(QSize(_TOGGLE_ICON_SIZE, _TOGGLE_ICON_SIZE))
        self.toggle_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.toggle_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.set_toggle_icons()
        header_layout.addWidget(self.toggle_button)
        self.addWidget(self.header)

        self.details = QWidget()
        details_layout = QVBoxLayout(self.details)
        details_layout.setContentsMargins(0, HALF_PAD, 0, 0)
        details_layout.setSpacing(HALF_PAD)
        self.folder_label = QLabel()
        self.folder_label.setTextFormat(Qt.TextFormat.RichText)
        self.folder_label.setWordWrap(True)
        self.folder_label.setTextInteractionFlags(Qt.TextInteractionFlag.LinksAccessibleByMouse)
        self._set_pixel_size(self.folder_label, _DETAILS_FONT_PIXEL_SIZE)
        self.folder_label.setIndent(HALF_PAD)
        self._add_file_actions(self.folder_label)
        details_layout.addWidget(self.folder_label)

        self._properties = QGridLayout()
        self._properties.setContentsMargins(0, 0, 0, 0)
        self._properties.setHorizontalSpacing(PAD * 2)
        self._properties.setVerticalSpacing(0)
        self._properties.setColumnStretch(1, 1)
        self._property_titles: dict[QLabel, QLabel] = {}
        self.size_label = self._add_property("file.size")
        self.dimensions_label = self._add_property("file.dimensions")
        self.duration_label = self._add_property("file.duration")
        self.font_family_label = self._add_property("file.font_family")
        self.font_style_label = self._add_property("file.font_style")
        self.date_added_label = self._add_property("file.date_added")
        self.date_created_label = self._add_property("file.date_created")
        self.date_modified_label = self._add_property("file.date_modified")
        details_layout.addLayout(self._properties)
        self.addWidget(self.details)
        self.addStretch(1)

    def set_property(self, value_label: QLabel, text: str | None) -> None:
        """Set a property's value, hiding its row when there's none."""
        value_label.setText(text or "")
        value_label.setHidden(text is None)
        self._property_titles[value_label].setHidden(text is None)

    def _add_property(self, title_key: str) -> QLabel:
        row = self._properties.rowCount()
        title_label = QLabel(Translations[title_key])
        opacity_effect = QGraphicsOpacityEffect(title_label)
        opacity_effect.setOpacity(0.5)
        title_label.setGraphicsEffect(opacity_effect)
        self._set_pixel_size(title_label, _DETAILS_FONT_PIXEL_SIZE)
        value_label = QLabel()
        self._set_pixel_size(value_label, _DETAILS_FONT_PIXEL_SIZE)
        value_label.setTextFormat(Qt.TextFormat.RichText)
        value_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        value_label.setWordWrap(True)
        title_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)
        self._properties.addWidget(title_label, row, 0, Qt.AlignmentFlag.AlignTop)
        self._properties.addWidget(value_label, row, 1, Qt.AlignmentFlag.AlignTop)
        self._property_titles[value_label] = title_label
        return value_label

    @staticmethod
    def _set_pixel_size(label: QLabel, size: int) -> None:
        font = label.font()
        font.setPixelSize(size)
        label.setFont(font)

    @staticmethod
    def _boxed_label(text_key: str, color: UiColor) -> QPushButton:
        label = QPushButton(Translations[text_key].upper())
        label.setCursor(Qt.CursorShape.PointingHandCursor)
        label.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        label.setStyleSheet(boxed_label_style(color=color))
        return label

    def _add_file_actions(self, widget: QWidget) -> None:
        widget.setContextMenuPolicy(Qt.ContextMenuPolicy.ActionsContextMenu)
        separator = QAction(widget)
        separator.setSeparator(True)
        widget.addActions(
            [
                self.open_file_action,
                self.open_explorer_action,
                separator,
                self.copy_filename_action,
                self.copy_path_action,
            ]
        )

    def set_toggle_icons(self) -> None:
        """Color the chevron toggles for the current theme."""
        self.expand_icon = svg_color_overlay(
            ResourceManager().chevron_down,
            theme_foreground_color(),
            self.toggle_button.devicePixelRatioF(),
            QSize(_TOGGLE_ICON_SIZE, _TOGGLE_ICON_SIZE),
        )
        self.collapse_icon = self.expand_icon.transformed(QTransform().scale(1, -1))
        self.collapse_icon.setDevicePixelRatio(self.expand_icon.devicePixelRatio())
