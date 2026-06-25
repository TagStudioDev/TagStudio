# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


import structlog
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QLabel,
    QLineEdit,
    QVBoxLayout,
    QWidget,
)

from tagstudio.qt.translations import Translations
from tagstudio.qt.views.panel_modal import PanelWidget

logger = structlog.get_logger(__name__)


class EditFieldTemplateModalView(PanelWidget):
    def __init__(self) -> None:
        super().__init__()

        # Layout Init
        self.setMinimumSize(460, 200)
        self.root_layout = QVBoxLayout(self)
        self.root_layout.setContentsMargins(6, 0, 6, 0)
        self.root_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Field Name -------------------------------------------------------------------------------
        self._name_widget = QWidget()
        self._name_layout = QVBoxLayout(self._name_widget)
        self._name_layout.setStretch(1, 1)
        self._name_layout.setContentsMargins(0, 0, 0, 0)
        self._name_layout.setSpacing(0)
        self._name_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self._name_title = QLabel(Translations["field.name"])
        self._name_layout.addWidget(self._name_title)
        self.name_field = QLineEdit()
        self.name_field.setFixedHeight(24)
        self.name_field.setPlaceholderText(Translations["field.field_name_required"])
        self._name_layout.addWidget(self.name_field)

        # Field Type -------------------------------------------------------------------------------
        self._type_widget = QWidget()
        self._type_layout = QVBoxLayout(self._type_widget)
        self._type_layout.setStretch(1, 1)
        self._type_layout.setContentsMargins(0, 0, 0, 0)
        self._type_layout.setSpacing(0)
        self._type_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self._type_title = QLabel(Translations["field.type"])
        self._type_layout.addWidget(self._type_title)
        self._type_combobox = QComboBox()
        self._type_layout.addWidget(self._type_combobox)

        # Add Widgets to Layout ====================================================================
        self.root_layout.addWidget(self._name_widget)
        self.root_layout.addWidget(self._type_widget)
