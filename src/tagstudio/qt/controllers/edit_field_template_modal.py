# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


import structlog

from tagstudio.core.library.alchemy.fields import (
    BaseFieldTemplate,
    DatetimeFieldTemplate,
    TextFieldTemplate,
)
from tagstudio.qt.models.palette import ColorType, UiColor, get_ui_color
from tagstudio.qt.translations import Translations
from tagstudio.qt.views.edit_field_template_modal_view import EditFieldTemplateModalView

logger = structlog.get_logger(__name__)


class EditFieldTemplateModal(EditFieldTemplateModalView):
    field_type_map: dict[str, str] = {
        "TextFieldTemplate": Translations["field_type.text"],
        "DatetimeFieldTemplate": Translations["field_type.datetime"],
    }
    DEFAULT_TYPE_INDEX = 0

    def __init__(self, field_template: BaseFieldTemplate | None = None) -> None:
        super().__init__()
        self.__field_id: int | None = field_template.id if field_template else None
        self.__field_name: str = ""
        self.__field_type: str | None = field_template.class_name if field_template else None
        self.old_field_type: str = ""

        for k, v in EditFieldTemplateModal.field_type_map.items():
            self._type_combobox.addItem(v, k)

        self.__connect_callbacks()
        self.set_field_template(field_template)
        self.__on_type_changed(EditFieldTemplateModal.DEFAULT_TYPE_INDEX)

    def __connect_callbacks(self) -> None:
        self.name_field.textChanged.connect(self.__on_name_changed)
        self._type_combobox.currentIndexChanged.connect(self.__on_type_changed)

    def set_field_template(self, field_template: BaseFieldTemplate | None = None) -> None:
        """Populate the modal with pre-existing field template values, or fallback to defaults."""
        logger.info("[EditFieldTemplate] Setting Field Template", field_template=field_template)

        # Indicates a new template, set default values
        if field_template is None:
            self.__field_name = Translations["field_template.new"]
            self.__field_type = list(EditFieldTemplateModal.field_type_map.keys())[
                EditFieldTemplateModal.DEFAULT_TYPE_INDEX
            ]
            return
        # Populate common values for any field type
        else:
            self.__field_name = field_template.name
            self.__field_type = field_template.class_name
            self.old_field_type = field_template.class_name  # Only set on init

        # Update widgets
        self.name_field.setText(self.__field_name)
        self._type_combobox.setCurrentIndex(
            list(EditFieldTemplateModal.field_type_map.keys()).index(field_template.class_name)
        )

        # Populate values for specific field types
        if isinstance(field_template, TextFieldTemplate):
            self._multiline_checkbox.setChecked(field_template.is_multiline)

    def __on_name_changed(self):
        is_empty = not self.name_field.text().strip()

        self.name_field.setStyleSheet(
            f"border: 1px solid {get_ui_color(ColorType.PRIMARY, UiColor.RED)}; border-radius: 2px"
            if is_empty
            else ""
        )

        if self.panel_save_button is not None:
            self.panel_save_button.setDisabled(is_empty)

    def __on_type_changed(self, index: int):
        old_type = self.__field_type
        self.__field_type = list(EditFieldTemplateModal.field_type_map.keys())[index]

        if old_type == self.__field_type:
            logger.info(f"old type {old_type}, new type {self.__field_type}")
            return

        if old_type == "TextFieldTemplate":
            self._text_field_attributes_widget.hide()
        # NOTE: Future options specific to other type will go here.

        if self.__field_type == "TextFieldTemplate":
            self._text_field_attributes_widget.show()

    def build_field_template(self) -> BaseFieldTemplate:
        if self.__field_type == "TextFieldTemplate":
            return TextFieldTemplate(
                id=self.__field_id,
                name=self.name_field.text(),
                is_multiline=self._multiline_checkbox.isChecked(),
            )
        elif self.__field_type == "DatetimeFieldTemplate":
            return DatetimeFieldTemplate(
                id=self.__field_id,
                name=self.name_field.text(),
            )
        else:
            logger.warning(
                "[EditFieldTemplateModal] Unknown field, falling back to TextFieldTemplate",
                field_type=self.__field_type,
                example=TextFieldTemplate,
            )
            return TextFieldTemplate(
                name=self.name_field.text(),
                is_multiline=self._multiline_checkbox.isChecked(),
            )
