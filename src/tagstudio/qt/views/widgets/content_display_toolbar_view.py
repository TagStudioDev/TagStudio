import typing

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QHBoxLayout,
    QCheckBox,
    QComboBox,
    QLabel,
    QWidget,
    QSpacerItem,
    QSizePolicy
    )
from tagstudio.core.library.alchemy.enums import SortingModeEnum, TagColorEnum
from tagstudio.qt.translations import Translations
from tagstudio.qt.models.thumb_sizes import THUMB_SIZES
from tagstudio.qt.mixed.tag_widget import get_border_color, get_highlight_color, get_text_color
from tagstudio.qt.models.palette import ColorType, get_tag_color


class ContentDisplayToolbar(QWidget):
    show_hidden_entries_widget: QWidget
    show_hidden_entries_layout: QHBoxLayout


    def __init__(self, parent: QWidget):
        super().__init__(parent)
        layout = QHBoxLayout()
        layout.setObjectName("content_display_toolbar") 

        primary_color = QColor(get_tag_color(ColorType.PRIMARY, TagColorEnum.DEFAULT))
        border_color = get_border_color(primary_color)
        highlight_color = get_highlight_color(primary_color)
        text_color: QColor = get_text_color(primary_color, highlight_color)

        ## Show hidden entries checkbox
        self.show_hidden_entries_widget = QWidget()
        self.show_hidden_entries_layout = QHBoxLayout(self.show_hidden_entries_widget)
        self.show_hidden_entries_layout.setStretch(1, 1)
        self.show_hidden_entries_layout.setContentsMargins(0, 0, 0, 0)
        self.show_hidden_entries_layout.setSpacing(6)
        self.show_hidden_entries_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.show_hidden_entries_title = QLabel(Translations["home.show_hidden_entries"])
        self.show_hidden_entries_checkbox = QCheckBox()
        self.show_hidden_entries_checkbox.setFixedSize(22, 22)

        self.show_hidden_entries_checkbox.setStyleSheet(
            f"QCheckBox{{"
            f"background: rgba{primary_color.toTuple()};"
            f"color: rgba{text_color.toTuple()};"
            f"border-color: rgba{border_color.toTuple()};"
            f"border-radius: 6px;"
            f"border-style:solid;"
            f"border-width: 2px;"
            f"}}"
            f"QCheckBox::indicator{{"
            f"width: 10px;"
            f"height: 10px;"
            f"border-radius: 2px;"
            f"margin: 4px;"
            f"}}"
            f"QCheckBox::indicator:checked{{"
            f"background: rgba{text_color.toTuple()};"
            f"}}"
            f"QCheckBox::hover{{"
            f"border-color: rgba{highlight_color.toTuple()};"
            f"}}"
            f"QCheckBox::focus{{"
            f"border-color: rgba{highlight_color.toTuple()};"
            f"outline:none;"
            f"}}"
        )

        self.show_hidden_entries_checkbox.setChecked(False)  # Default: No

        self.show_hidden_entries_layout.addWidget(self.show_hidden_entries_checkbox)
        self.show_hidden_entries_layout.addWidget(self.show_hidden_entries_title)

        layout.addWidget(self.show_hidden_entries_widget)

        ## Spacer
        layout.addItem(
            QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        )

        ## Sorting Mode Dropdown
        self.sorting_mode_combobox = QComboBox(self)
        self.sorting_mode_combobox.setObjectName("sorting_mode_combobox")
        for sort_mode in SortingModeEnum:
            self.sorting_mode_combobox.addItem(Translations[sort_mode.value], sort_mode)
        layout.addWidget(self.sorting_mode_combobox)

        ## Sorting Direction Dropdown
        self.sorting_direction_combobox = QComboBox(self)
        self.sorting_direction_combobox.setObjectName("sorting_direction_combobox")
        self.sorting_direction_combobox.addItem(
            Translations["sorting.direction.ascending"], userData=True
        )
        self.sorting_direction_combobox.addItem(
            Translations["sorting.direction.descending"], userData=False
        )
        self.sorting_direction_combobox.setCurrentIndex(1)  # Default: Descending
        layout.addWidget(self.sorting_direction_combobox)

        ## Thumbnail Size placeholder
        self.thumb_size_combobox = QComboBox(self)
        self.thumb_size_combobox.setObjectName("thumb_size_combobox")
        self.thumb_size_combobox.setPlaceholderText(Translations["home.thumbnail_size"])
        self.thumb_size_combobox.setCurrentText("")
        size_policy = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        size_policy.setHorizontalStretch(0)
        size_policy.setVerticalStretch(0)
        size_policy.setHeightForWidth(self.thumb_size_combobox.sizePolicy().hasHeightForWidth())
        self.thumb_size_combobox.setSizePolicy(size_policy)
        self.thumb_size_combobox.setMinimumWidth(128)
        self.thumb_size_combobox.setMaximumWidth(352)
        layout.addWidget(self.thumb_size_combobox)
        for size in THUMB_SIZES:
            self.thumb_size_combobox.addItem(size[0], size[1])
        self.thumb_size_combobox.setCurrentIndex(2)  # Default: Medium

        self.setLayout(layout)