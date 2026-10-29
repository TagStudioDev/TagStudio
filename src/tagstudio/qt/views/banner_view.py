# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QPushButton, QVBoxLayout

from tagstudio.i18n.translations import Translations
from tagstudio.qt.controllers.rounded_progress_bar import RoundedProgressBar
from tagstudio.qt.controllers.stable_label import StableLabel
from tagstudio.qt.views.styles.widget_effects import DEBOSSED_OUTLINE_WIDTH


class BannerView(QVBoxLayout):
    PROGRESS_BAR_HEIGHT = 4

    def __init__(self) -> None:
        super().__init__()
        self.setContentsMargins(
            DEBOSSED_OUTLINE_WIDTH, 0, DEBOSSED_OUTLINE_WIDTH, DEBOSSED_OUTLINE_WIDTH
        )
        self.setSpacing(0)

        content_row = QHBoxLayout()
        content_row.setContentsMargins(
            6 - DEBOSSED_OUTLINE_WIDTH, 6, 6 - DEBOSSED_OUTLINE_WIDTH, 2 - DEBOSSED_OUTLINE_WIDTH
        )
        content_row.setSpacing(8)

        self.close_button = QPushButton("×")
        self.close_button.setObjectName("bannerCloseButton")
        self.close_button.setFixedSize(24, 24)
        self.close_button.setFocusPolicy(Qt.FocusPolicy.TabFocus)
        content_row.addWidget(self.close_button)

        content_row.addStretch(1)

        self.label = StableLabel()
        content_row.addWidget(self.label)

        self.action_button = QPushButton(Translations["entries.generic.refresh_alt"])
        self.action_button.setObjectName("bannerActionButton")
        self.action_button.setFocusPolicy(Qt.FocusPolicy.TabFocus)
        content_row.addWidget(self.action_button)

        content_row.addStretch(1)
        self.addLayout(content_row, 1)

        self.progress_bar = RoundedProgressBar()
        self.progress_bar.setFixedHeight(self.PROGRESS_BAR_HEIGHT)

        policy = self.progress_bar.sizePolicy()
        policy.setRetainSizeWhenHidden(True)
        self.progress_bar.setSizePolicy(policy)
        self.addWidget(self.progress_bar)
