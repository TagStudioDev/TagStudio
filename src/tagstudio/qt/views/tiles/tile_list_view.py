# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QScrollArea, QSizePolicy, QVBoxLayout, QWidget

from tagstudio.qt.views.styles.stylesheets import HALF_PAD, PAD, inset_container_style


class TileListView(QHBoxLayout):
    def __init__(self) -> None:
        super().__init__()
        self.setContentsMargins(0, 0, 0, 0)

        self.scroll_layout = QVBoxLayout()
        self.scroll_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.scroll_layout.setContentsMargins(HALF_PAD, HALF_PAD, HALF_PAD, HALF_PAD)
        self.scroll_layout.setSpacing(PAD)

        scroll_container = QWidget()
        scroll_container.setObjectName("tile_scroll_container")
        scroll_container.setLayout(self.scroll_layout)

        self.scroll_area = QScrollArea()
        self.scroll_area.setObjectName("tile_scroll_area")
        self.scroll_area.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShadow(QFrame.Shadow.Plain)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)

        # NOTE: I would rather have this style applied to the scroll_area
        # background and NOT the scroll container background, so that the
        # rounded corners are maintained when scrolling. I was unable to
        # find the right trick to only select that particular element.
        self.scroll_area.setStyleSheet(inset_container_style("tile_scroll_container"))
        self.scroll_area.setWidget(scroll_container)

        self.addWidget(self.scroll_area)
