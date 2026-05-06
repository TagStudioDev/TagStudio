from collections.abc import Iterable

from PySide6.QtWidgets import QPushButton

from tagstudio.core.library.alchemy.enums import TagColorEnum
from tagstudio.core.library.alchemy.models import TagColorGroup
from tagstudio.core.utils.types import unwrap
from tagstudio.qt.mixed.tag_color_label import TagColorLabel
from tagstudio.qt.models.palette import ColorType, get_tag_color
from tagstudio.qt.views.field_widget_view import FieldWidgetView
from tagstudio.qt.views.layouts.flow_layout import FlowLayout


class TagColorBoxWidgetView(FieldWidgetView):
    """A widget holding a list of tag colors."""

    def __init__(self, title: str):
        super().__init__(title)

        self.setObjectName("colorBox")

        self.__root_layout = FlowLayout()
        self.__root_layout.enable_grid_optimizations(value=False)
        self.__root_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.__root_layout)

        self.color_widgets: list[TagColorLabel] = []

        self.add_button_stylesheet: str = (
            f"QPushButton{{"
            f"background: {get_tag_color(ColorType.PRIMARY, TagColorEnum.DEFAULT)};"
            f"color: {get_tag_color(ColorType.TEXT, TagColorEnum.DEFAULT)};"
            f"font-weight: 600;"
            f"border-color:{get_tag_color(ColorType.BORDER, TagColorEnum.DEFAULT)};"
            f"border-radius: 6px;"
            f"border-style:solid;"
            f"border-width: 2px;"
            f"padding-right: 4px;"
            f"padding-bottom: 2px;"
            f"padding-left: 4px;"
            f"font-size: 15px"
            f"}}"
            f"QPushButton::hover{{"
            f"border-color:{get_tag_color(ColorType.LIGHT_ACCENT, TagColorEnum.DEFAULT)};"
            f"}}"
            f"QPushButton::pressed{{"
            f"background: {get_tag_color(ColorType.LIGHT_ACCENT, TagColorEnum.DEFAULT)};"
            f"color: {get_tag_color(ColorType.PRIMARY, TagColorEnum.DEFAULT)};"
            f"border-color: {get_tag_color(ColorType.PRIMARY, TagColorEnum.DEFAULT)};"
            f"}}"
            f"QPushButton::focus{{"
            f"border-color: {get_tag_color(ColorType.LIGHT_ACCENT, TagColorEnum.DEFAULT)};"
            f"outline:none;"
            f"}}"
        )

        self.__add_button = QPushButton()
        self.__add_button.setText("+")
        self.__add_button.setFlat(True)
        self.__add_button.setFixedSize(22, 22)
        self.__add_button.setStyleSheet(self.add_button_stylesheet)
        self.__add_button.setHidden(True)

        self.__connect_callbacks()

    def __connect_callbacks(self) -> None:
        self.__add_button.clicked.connect(self._on_add_color)

    def set_colors(self, colors: Iterable[TagColorGroup], is_mutable: bool) -> None:
        """Sets the colors the color box contains."""
        max_width: int = 60

        self.remove_contents()

        for color in colors:
            color_widget: TagColorLabel = self.add_color_widget(color, is_mutable)

            color_widget.on_click.connect(lambda c=color: self._on_edit_color(c))
            color_widget.on_remove.connect(lambda c=color: self._on_delete_color(c))

            widget_width: int = color_widget.sizeHint().width()
            if widget_width > max_width:
                max_width = widget_width

        for color_widget in self.color_widgets:
            color_widget.setFixedWidth(max_width)

        self.update_add_button(is_mutable)

    def add_color_widget(self, color: TagColorGroup, is_mutable: bool) -> TagColorLabel:
        """Adds a color widget to the color box."""
        color_widget: TagColorLabel = TagColorLabel(
            color=color, has_edit=is_mutable, has_remove=is_mutable
        )

        self.color_widgets.append(color_widget)
        self.__root_layout.addWidget(color_widget)

        return color_widget

    def remove_contents(self) -> None:
        """Removes all the color widgets from the color box."""
        while self.__root_layout.itemAt(0):
            unwrap(self.__root_layout.takeAt(0)).widget().deleteLater()

        self.color_widgets = []

    def update_add_button(self, is_mutable: bool) -> None:
        """Moves the add button to the end and updates its visibility."""
        self.__add_button.setVisible(False)
        self.__root_layout.removeWidget(self.__add_button)
        self.__root_layout.addWidget(self.__add_button)
        self.__add_button.setVisible(is_mutable)

    def _on_add_color(self) -> None | NotImplementedError:
        return NotImplementedError()

    def _on_edit_color(self, color_group: TagColorGroup) -> None | NotImplementedError:
        return NotImplementedError()

    def _on_delete_color(self, color_group: TagColorGroup) -> None | NotImplementedError:
        return NotImplementedError()
