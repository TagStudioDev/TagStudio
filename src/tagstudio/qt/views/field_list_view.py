from PySide6.QtCore import Qt
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QFrame, QHBoxLayout, QScrollArea, QSizePolicy, QVBoxLayout, QWidget

from tagstudio.core.enums import Theme
from tagstudio.qt.mixed.field_widget import FieldContainer


class FieldListView(QWidget):
    def __init__(self):
        super().__init__()

        self.field_containers: list[FieldContainer] = []

        self.panel_bg_color = (
            Theme.COLOR_BG_DARK.value
            if QGuiApplication.styleHints().colorScheme() is Qt.ColorScheme.Dark
            else Theme.COLOR_BG_LIGHT.value
        )

        self.scroll_layout = QVBoxLayout()
        self.scroll_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.scroll_layout.setContentsMargins(3, 3, 3, 3)
        self.scroll_layout.setSpacing(0)

        scroll_container: QWidget = QWidget()
        scroll_container.setObjectName("entryScrollContainer")
        scroll_container.setLayout(self.scroll_layout)

        info_section = QWidget()
        info_layout = QVBoxLayout(info_section)
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(0)

        self.scroll_area = QScrollArea()
        self.scroll_area.setObjectName("entryScrollArea")
        self.scroll_area.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShadow(QFrame.Shadow.Plain)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)

        # NOTE: I would rather have this style applied to the scroll_area
        # background and NOT the scroll container background, so that the
        # rounded corners are maintained when scrolling. I was unable to
        # find the right trick to only select that particular element.
        self.scroll_area.setStyleSheet(
            f"QWidget#entryScrollContainer{{background:{self.panel_bg_color};border-radius:6px;}}"
        )
        self.scroll_area.setWidget(scroll_container)

        root_layout = QHBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.addWidget(self.scroll_area)

    def hide_all(self):
        """Hide all field and tag containers."""
        for field_container in self.field_containers:
            field_container.setHidden(True)

    def hide_after(self, after_index: int):
        for index, field_container in enumerate(self.field_containers):
            if index >= after_index:
                field_container.setHidden(True)
