# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


import structlog
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QVBoxLayout,
    QWidget,
)

from tagstudio.qt.controllers.clickable_label import ClickableLabel
from tagstudio.qt.controllers.modal_content import ModalContent
from tagstudio.qt.translations import Translations
from tagstudio.qt.views.stylesheets.stylesheets import checkbox_style

logger = structlog.get_logger(__name__)


class EditFieldTemplateModalView(ModalContent):
    def __init__(self) -> None:
        super().__init__()

        # Layout Init
        self.setMinimumSize(460, 200)
        self.root_layout = QVBoxLayout(self)
        self.root_layout.setContentsMargins(6, 0, 6, 0)
        self.root_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Field Name
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

        # Field Type
        self._type_widget = QWidget()
        self._type_layout = QVBoxLayout(self._type_widget)
        self._type_layout.setStretch(1, 1)
        self._type_layout.setContentsMargins(0, 0, 0, 0)
        self._type_layout.setSpacing(0)
        self._type_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self._type_title = QLabel(Translations["field.type"])
        self._type_layout.addWidget(self._type_title)
        self._type_combobox = QComboBox()
        self._type_combobox.setMinimumWidth(120)
        self._type_layout.addWidget(self._type_combobox)

        # Text Field Attributes --------------------------------------------------------------------
        self._text_field_attributes_widget = QWidget()
        self._text_field_attributes_layout = QHBoxLayout(self._text_field_attributes_widget)
        self._text_field_attributes_layout.setStretch(1, 1)
        self._text_field_attributes_layout.setContentsMargins(0, 0, 0, 0)
        self._text_field_attributes_layout.setSpacing(6)

        # Is Multiline
        self._multiline_widget = QWidget()
        self._multiline_layout = QHBoxLayout(self._multiline_widget)
        self._multiline_layout.setStretch(1, 1)
        self._multiline_layout.setContentsMargins(0, 0, 0, 0)
        self._multiline_layout.setSpacing(6)
        self._multiline_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self._multiline_title = ClickableLabel(Translations["field.text.is_multiline"])
        self._multiline_checkbox = QCheckBox()
        self._multiline_checkbox.setFixedSize(22, 22)
        self._multiline_checkbox.setStyleSheet(checkbox_style())
        self._multiline_title.clicked.connect(self._multiline_checkbox.click)
        self._multiline_layout.addWidget(self._multiline_checkbox)
        self._multiline_layout.addWidget(self._multiline_title)
        self._text_field_attributes_layout.addWidget(self._multiline_widget)

        # NOTE: Future options specific to other type will go in their own sections,
        # following the pattern with text fields above.

        # Add Widgets to Layout ====================================================================
        self.root_layout.addWidget(self._name_widget)
        self.root_layout.addWidget(self._type_widget)
        self.root_layout.addWidget(self._text_field_attributes_widget)
