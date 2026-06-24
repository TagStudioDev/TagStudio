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

    def __init__(self, field_template: BaseFieldTemplate | None = None) -> None:
        super().__init__()
        self.__field_id: int = field_template.id if field_template else -1
        self.__field_name: str = ""
        self.__field_type: str | None = field_template.class_name if field_template else None
        self.__text_field_is_multiline: bool = False
        self.old_field_type: str = ""

        for k, v in EditFieldTemplateModal.field_type_map.items():
            self._type_combobox.addItem(v, k)

        self.__connect_callbacks()
        self.set_field_template(field_template)

    def __connect_callbacks(self) -> None:
        self.name_field.textChanged.connect(self.__on_name_changed)
        self._type_combobox.currentIndexChanged.connect(self.__on_type_changed)

    def set_field_template(self, field_template: BaseFieldTemplate | None = None) -> None:
        """Populate the modal with pre-existing field template values, or fallback to defaults."""
        logger.info("[EditFieldTemplate] Setting Field Template", field_template=field_template)

        # Indicates a new template, set default values
        if field_template is None:
            self.__field_name = Translations["field_template.new"]
            self.__field_type = None
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
            self.__text_field_is_multiline = field_template.is_multiline

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
        self.__field_type = list(EditFieldTemplateModal.field_type_map.keys())[index]

    def build_field_template(self) -> BaseFieldTemplate:
        if self.__field_type == "TextFieldTemplate":
            return TextFieldTemplate(
                id=self.__field_id,
                name=self.name_field.text(),
                is_multiline=self.__text_field_is_multiline,
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
                is_multiline=self.__text_field_is_multiline,
            )

    # def parent_post_init(self):
    #     self.setTabOrder(self.name_field, self.shorthand_field)
    #     self.setTabOrder(self.shorthand_field, self.aliases_add_button)
    #     self.setTabOrder(self.aliases_add_button, self.parent_tags_add_button)
    #     self.setTabOrder(self.parent_tags_add_button, self.color_button)
    #     self.setTabOrder(self.color_button, unwrap(self.panel_cancel_button))
    #     self.setTabOrder(unwrap(self.panel_cancel_button), unwrap(self.panel_save_button))
    #     self.setTabOrder(unwrap(self.panel_save_button), self.aliases_table.cellWidget(0, 1))
    #     self.name_field.selectAll()
    #     self.name_field.setFocus()
    #     self._set_aliases()
