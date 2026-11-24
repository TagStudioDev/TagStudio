# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


from PySide6.QtCore import Qt
from PySide6.QtWidgets import QVBoxLayout

from tagstudio.qt.controllers.inset_scroll_box import InsetScrollBox
from tagstudio.qt.views.layouts.capsule_flow_layout import CapsuleFlowLayout


class CapsuleBoxView(QVBoxLayout):
    def __init__(self) -> None:
        super().__init__()
        self.setContentsMargins(0, 0, 0, 0)

        self.capsule_layout = CapsuleFlowLayout()

        self.scroll_box = InsetScrollBox()
        scroll_box_view = self.scroll_box.layout()
        scroll_box_view.scroll_layout.addLayout(self.capsule_layout)
        scroll_box_view.scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.addWidget(self.scroll_box)
