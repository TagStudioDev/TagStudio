# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QScrollArea, QVBoxLayout, QWidget

from tagstudio.qt.controllers.inset_frame import InsetFrame
from tagstudio.qt.views.styles.stylesheets import PAD
from tagstudio.qt.views.styles.tagstudio_style import set_track_side_inset
from tagstudio.qt.views.styles.widget_effects import DEBOSSED_OUTLINE_WIDTH


class InsetScrollBoxView(QVBoxLayout):
    def __init__(self) -> None:
        super().__init__()
        self.setContentsMargins(0, 0, 0, 0)

        self.scroll_contents = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_contents)
        # Inside the scrolled content so the padding scrolls with it
        padding = PAD - DEBOSSED_OUTLINE_WIDTH
        self.scroll_layout.setContentsMargins(0, padding, 0, padding)

        self.scroll_area = QScrollArea()
        self.scroll_area.setStyleSheet("QScrollArea { background: transparent; }")
        self.scroll_area.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.scroll_area.setWidget(self.scroll_contents)
        # NOTE: setWidget() turns this on
        self.scroll_contents.setAutoFillBackground(False)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        # Center the scroll bar between the content and the box's edge
        set_track_side_inset(self.scroll_area.verticalScrollBar(), DEBOSSED_OUTLINE_WIDTH)

        frame = InsetFrame()
        self.frame_layout = QVBoxLayout(frame)
        self.frame_layout.setContentsMargins(PAD, DEBOSSED_OUTLINE_WIDTH, 0, DEBOSSED_OUTLINE_WIDTH)
        self.frame_layout.addWidget(self.scroll_area)
        self.addWidget(frame)
