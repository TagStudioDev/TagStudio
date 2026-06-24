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
        self.__name_widget = QWidget()
        self.__name_layout = QVBoxLayout(self.__name_widget)
        self.__name_layout.setStretch(1, 1)
        self.__name_layout.setContentsMargins(0, 0, 0, 0)
        self.__name_layout.setSpacing(0)
        self.__name_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.__name_title = QLabel(Translations["field.name"])
        self.__name_layout.addWidget(self.__name_title)
        self.name_field = QLineEdit()
        self.name_field.setFixedHeight(24)
        self.name_field.setPlaceholderText(Translations["field.field_name_required"])
        self.__name_layout.addWidget(self.name_field)

        # Field Type -------------------------------------------------------------------------------
        self.__type_widget = QWidget()
        self.__type_layout = QVBoxLayout(self.__type_widget)
        self.__type_layout.setStretch(1, 1)
        self.__type_layout.setContentsMargins(0, 0, 0, 0)
        self.__type_layout.setSpacing(0)
        self.__type_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.__type_title = QLabel(Translations["field.type"])
        self.__type_layout.addWidget(self.__type_title)
        self._type_combobox = QComboBox()
        self.__type_layout.addWidget(self._type_combobox)

        # Add Widgets to Layout ====================================================================
        self.root_layout.addWidget(self.__name_widget)
        self.root_layout.addWidget(self.__type_widget)
