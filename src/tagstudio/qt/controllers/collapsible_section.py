# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


from typing import override

from PySide6.QtCore import QEvent, QSize, Qt
from PySide6.QtGui import QTransform
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QSizePolicy, QVBoxLayout, QWidget

from tagstudio.qt.resource_manager import ResourceManager
from tagstudio.qt.views.styles.color_overlay import svg_color_overlay, theme_foreground_color
from tagstudio.qt.views.styles.stylesheets import HALF_PAD, header, icon_button_style

_TITLE_ICON_SIZE = QSize(18, 18)


class CollapsibleSection(QWidget):
    """A collapsable panel section."""

    def __init__(
        self, svg: bytes, title: str, *contents: QWidget, caret_row: QHBoxLayout | None = None
    ) -> None:
        super().__init__()
        self.is_collapsed = False
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(HALF_PAD)

        self._header_layout = QHBoxLayout()
        self._header_layout.setContentsMargins(0, 0, 0, 0)
        self._header_layout.setSpacing(HALF_PAD)
        self._svg = svg
        self._icon_label = QLabel()
        self.collapse_button = self._new_caret_button()
        self._row_caret_button: QPushButton | None = None
        if caret_row is not None:
            caret_row.setSpacing(HALF_PAD)
            self._row_caret_button = self._new_caret_button()
            self._row_caret_button.clicked.connect(self.collapse_button.click)
            caret_row.addWidget(self._row_caret_button)
        self._set_icons()
        self._header_layout.addWidget(self._icon_label)
        self._title_label = QLabel(header(title, 4))
        self._title_label.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self._header_layout.addWidget(self._title_label, stretch=1)
        self._header_layout.addWidget(self.collapse_button)
        layout.addLayout(self._header_layout)
        self._set_title_shown(caret_row is None)

        self._contents = QWidget()
        self._contents_max_height = self._contents.maximumHeight()
        contents_layout = QVBoxLayout(self._contents)
        contents_layout.setContentsMargins(0, 0, 0, 0)
        contents_layout.setSpacing(HALF_PAD)
        for widget in contents:
            contents_layout.addWidget(widget, stretch=1)
        layout.addWidget(self._contents, stretch=1)
        layout.addStretch()  # Keeps the title in place while the contents are hidden

    @override
    def changeEvent(self, event: QEvent) -> None:
        if event.type() == QEvent.Type.ThemeChange:
            self._set_icons()
        super().changeEvent(event)

    @property
    def header_height(self) -> int:
        return max(self._title_label.sizeHint().height(), _TITLE_ICON_SIZE.height())

    def set_collapsed(self, collapsed: bool) -> None:
        self.is_collapsed = collapsed
        self._set_collapse_icon()

    def _new_caret_button(self) -> QPushButton:
        button = QPushButton()
        button.setFlat(True)
        button.setStyleSheet(icon_button_style())
        button.setFixedSize(_TITLE_ICON_SIZE)
        button.setIconSize(_TITLE_ICON_SIZE)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        return button

    def _set_title_shown(self, shown: bool) -> None:
        for widget in (self._icon_label, self._title_label, self.collapse_button):
            widget.setHidden(not shown)

    def fit_contents(self, height: float) -> None:
        """Limit the contents to fit within this section height."""
        section_height = min(round(height), self.height())
        if self._row_caret_button is None:
            contents_height = max(0, section_height - self.header_height - HALF_PAD)
        else:
            # Swaps with the title once the field no longer fits
            is_contents_fit = section_height >= self._contents.minimumSizeHint().height()
            contents_height = section_height if is_contents_fit else 0
            self._set_title_shown(not is_contents_fit)
        self._contents.setMaximumHeight(contents_height)
        self._contents.setHidden(contents_height == 0)

    def finish_contents(self) -> None:
        # Hide the contents if collapsed and stop limiting their height
        self._contents.setMaximumHeight(self._contents_max_height)
        self._contents.setHidden(self.is_collapsed)
        self._set_title_shown(self._row_caret_button is None or self.is_collapsed)

    def _set_icons(self) -> None:
        pixel_ratio = self._icon_label.devicePixelRatioF()
        self._icon_label.setPixmap(
            svg_color_overlay(self._svg, theme_foreground_color(), pixel_ratio, _TITLE_ICON_SIZE)
        )
        self._expand_icon = svg_color_overlay(
            ResourceManager().chevron_down, theme_foreground_color(), pixel_ratio, _TITLE_ICON_SIZE
        )
        self._collapse_icon = self._expand_icon.transformed(QTransform().scale(1, -1))
        self._collapse_icon.setDevicePixelRatio(self._expand_icon.devicePixelRatio())
        self._set_collapse_icon()

    def _set_collapse_icon(self) -> None:
        icon = self._expand_icon if self.is_collapsed else self._collapse_icon
        self.collapse_button.setIcon(icon)
        if self._row_caret_button is not None:
            self._row_caret_button.setIcon(icon)
