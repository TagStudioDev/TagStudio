from PySide6.QtCore import Qt
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QFrame, QHBoxLayout, QScrollArea, QSizePolicy, QVBoxLayout, QWidget

from tagstudio.core.enums import Theme
from tagstudio.qt.controllers.field_container_controller import FieldContainer


class FieldListView(QWidget):
    def __init__(self) -> None:
        super().__init__()

        self.field_containers: list[FieldContainer] = []

        self.panel_bg_color: str = (
            Theme.COLOR_BG_DARK.value
            if QGuiApplication.styleHints().colorScheme() is Qt.ColorScheme.Dark
            else Theme.COLOR_BG_LIGHT.value
        )

        # Field list
        self.setObjectName("field_list")

        self.__root_layout = QHBoxLayout(self)
        self.__root_layout.setContentsMargins(0, 0, 0, 0)

        self.setLayout(self.__root_layout)

        # Scroll area
        self.__scroll_area = QScrollArea()
        self.__scroll_area.setObjectName("entry_scroll_area")

        self.__scroll_area.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.__scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.__scroll_area.setWidgetResizable(True)
        self.__scroll_area.setFrameShadow(QFrame.Shadow.Plain)
        self.__scroll_area.setFrameShape(QFrame.Shape.NoFrame)

        self.__root_layout.addWidget(self.__scroll_area)

        # Scroll container
        self.scroll_layout = QVBoxLayout()
        self.scroll_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.scroll_layout.setContentsMargins(3, 3, 3, 3)
        self.scroll_layout.setSpacing(0)

        self.scroll_container: QWidget = QWidget()
        self.scroll_container.setObjectName("entry_scroll_container")
        self.scroll_container.setLayout(self.scroll_layout)

        self.__scroll_area.setWidget(self.scroll_container)

        # NOTE: I would rather have this style applied to the scroll_area
        # background and NOT the scroll container background, so that the
        # rounded corners are maintained when scrolling. I was unable to
        # find the right trick to only select that particular element.
        self.__scroll_area.setStyleSheet(
            f"""
                QWidget#entry_scroll_container{{
                    background: {self.panel_bg_color};
                    border-radius: 6px;
                }}
            """
        )

    def hide_all(self) -> None:
        """Hide all field and tag containers."""
        for field_container in self.field_containers:
            field_container.setHidden(True)

    def hide_after(self, after_index: int) -> None:
        """Hide all field containers after a certain index."""
        for index, field_container in enumerate(self.field_containers):
            if index >= after_index:
                field_container.setHidden(True)
