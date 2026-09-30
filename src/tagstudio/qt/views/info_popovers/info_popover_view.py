# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget

from tagstudio.core.library.alchemy.models import TagColorGroup
from tagstudio.qt.controllers.capsule import Capsule
from tagstudio.qt.resource_manager import ResourceManager
from tagstudio.qt.views.styles.color_overlay import svg_to_pixmap, theme_foreground_color
from tagstudio.qt.views.styles.stylesheets import header, info_popover_text_style


class InfoPopoverView(QVBoxLayout):
    """Base layout for info popover content.

    Includes some common visual examples and helper functions.
    """

    _ROW_SPACING = 3  # TODO: Use future constant from stylesheets.py

    def __init__(self) -> None:
        super().__init__()
        self.setContentsMargins(0, 0, 0, 0)
        self.setSpacing(6)

    def _text_label(self, text: str) -> QLabel:
        label = QLabel(info_popover_text_style() + text)
        label.setTextFormat(Qt.TextFormat.RichText)
        label.setWordWrap(True)
        return label

    def _add_section(self, title: str, description: str, header_level: int = 4) -> None:
        """Add a text section to the info popover."""
        if self.count():
            self.addSpacing(6)  # Add to the layout's spacing for 12px total between sections
        section = QWidget()
        layout = QVBoxLayout(section)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)  # Space between the header and description text
        layout.addWidget(self._text_label(header(title, header_level)))
        layout.addWidget(self._text_label(description))
        self.addWidget(section)

    def _icon_label(self, svg: bytes, size: QSize | None = None) -> QLabel:
        label = QLabel()
        label.setPixmap(
            svg_to_pixmap(svg, theme_foreground_color(), label.devicePixelRatioF(), size)
        )
        return label

    def _dim_label(self, text: str) -> QLabel:
        """A dim italic label, used best as a note next to a widget."""
        label = QLabel(f"<i>{text}</i>")
        label.setStyleSheet(f"color: rgba{theme_foreground_color().getRgb()}; padding-left: 3px;")
        label.setIndent(0)
        return label

    def _example(self, *rows: QWidget) -> QWidget:
        """Group rows of example widgets and make them non-interactive."""
        widget = QWidget()
        widget.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(3)
        for row in rows:
            layout.addWidget(row)
        return widget

    def _example_row(self, *widgets: QWidget, indent: int = 0) -> QWidget:
        row = QWidget()
        layout = QHBoxLayout(row)
        layout.setContentsMargins(indent, 0, 0, 0)
        layout.setSpacing(self._ROW_SPACING)
        for widget in widgets:
            layout.addWidget(widget)
        layout.addStretch(1)
        return row

    def _example_capsule(
        self, text: str, color_group: TagColorGroup | None = None, min_width: int = 0
    ) -> Capsule:
        capsule = Capsule()
        capsule.set_text(text)
        capsule.set_color_group(color_group)
        capsule.layout().button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        capsule.layout().remove_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        if min_width:
            capsule.setMinimumWidth(min_width)
        return capsule

    def _example_tree(self, *levels: list[QWidget]) -> QWidget:
        """An indented hierarchical tree of widgets."""
        tree_arrow_center = 5  # Visual center of the angled arrow's stem

        rows = [self._example_row(*levels[0])]
        parent_left, parent_width = 0, levels[0][0].sizeHint().width()
        for widgets in levels[1:]:
            arrow = self._icon_label(ResourceManager().arrow_right_bottom)
            # Keep rows as tall as their tags so the gaps between rows match the layout spacing
            arrow.setFixedHeight(widgets[0].sizeHint().height())
            # Start each angled arrow's stem 25% of the way into the tag above it
            indent = round(parent_left + parent_width * 0.25 - tree_arrow_center)
            rows.append(self._example_row(arrow, *widgets, indent=indent))
            parent_left = indent + arrow.sizeHint().width() + self._ROW_SPACING
            parent_width = widgets[0].sizeHint().width()
        return self._example(*rows)

    def _example_result(self, example: QWidget, result: QWidget) -> QWidget:
        """Show an "A -> B" type example of two widgets."""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(9)  # Adds to the arrow's own 3px padding for 12px on each side
        layout.addWidget(example, alignment=Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(self._icon_label(ResourceManager().arrow_right))
        layout.addWidget(result, stretch=1, alignment=Qt.AlignmentFlag.AlignVCenter)
        return widget
