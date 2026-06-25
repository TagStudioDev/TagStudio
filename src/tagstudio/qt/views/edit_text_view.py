# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


from PySide6.QtGui import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QHBoxLayout,
    QLineEdit,
    QPlainTextEdit,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from tagstudio.qt.controllers.clickable_label import ClickableLabel
from tagstudio.qt.translations import Translations
from tagstudio.qt.views.panel_modal import PanelWidget
from tagstudio.qt.views.stylesheets.stylesheets import checkbox_style


class EditTextView(PanelWidget):
    def __init__(self):
        super().__init__()
        self.setMinimumSize(480, 240)
        self.root_layout = QVBoxLayout(self)
        self.root_layout.setContentsMargins(6, 0, 6, 0)

        self.name_field = QLineEdit()
        self.name_field.setStyleSheet("font-weight:bold;font-size:14px;padding-top:6px")

        self.text_box = QPlainTextEdit()
        self.text_line = QLineEdit()
        self.text_line_stretch = QWidget()
        self.text_line_stretch.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )

        # Is Multiline
        self.multiline_widget = QWidget()
        self.multiline_layout = QHBoxLayout(self.multiline_widget)
        self.multiline_layout.setStretch(1, 1)
        self.multiline_layout.setContentsMargins(0, 0, 0, 0)
        self.multiline_layout.setSpacing(6)
        self.multiline_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.multiline_title = ClickableLabel(Translations["field.text.is_multiline"])
        self.multiline_checkbox = QCheckBox()
        self.multiline_checkbox.setFixedSize(22, 22)
        self.multiline_checkbox.setStyleSheet(checkbox_style())
        self.multiline_title.clicked.connect(self.multiline_checkbox.click)
        self.multiline_layout.addWidget(self.multiline_checkbox)
        self.multiline_layout.addWidget(self.multiline_title)

        self.root_layout.addWidget(self.name_field)
        self.root_layout.addWidget(self.text_box)
        self.root_layout.setStretch(2, 1)
        self.root_layout.addWidget(self.text_line)
        self.root_layout.addWidget(self.text_line_stretch)
        self.root_layout.setStretch(4, 1)
        self.root_layout.addWidget(self.multiline_widget)
