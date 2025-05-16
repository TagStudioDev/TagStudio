# Copyright (C) 2025 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio


import logging
import typing

from PySide6.QtCore import QMetaObject, QSize, QStringListModel, Qt
from PySide6.QtWidgets import (
    QComboBox,
    QCompleter,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLayout,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpacerItem,
    QSplitter,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from tagstudio.qt.pagination import Pagination
from tagstudio.qt.translations import Translations
from tagstudio.qt.widgets.landing import LandingWidget

# Only import for type checking/autocompletion, will not be imported at runtime.
if typing.TYPE_CHECKING:
    from tagstudio.qt.ts_qt import QtDriver

logging.basicConfig(format="%(message)s", level=logging.INFO)


# View Component
class MainWindow(QMainWindow):
    def __init__(self, driver: "QtDriver", parent=None) -> None:
        super().__init__(parent)

        if not self.objectName():
            self.setObjectName("MainWindow")
        self.resize(1300, 720)

        # region Central Widget
        self.central_widget = QWidget(self)
        self.central_widget.setObjectName("centralwidget")
        self.central_layout = QGridLayout(self.central_widget)
        self.central_layout.setObjectName("centralLayout")

        # region Search Bar:        Nav Buttons, Search Field, Search Button
        nav_button_style = "font-size:14;font-weight:bold;"
        self.search_bar_layout = QHBoxLayout()
        self.search_bar_layout.setObjectName("search_bar_layout")
        self.search_bar_layout.setSizeConstraint(QLayout.SizeConstraint.SetMinimumSize)

        self.back_button = QPushButton("<", self.central_widget)
        self.back_button.setObjectName("backButton")
        self.back_button.setMinimumSize(QSize(0, 32))
        self.back_button.setMaximumSize(QSize(32, 16777215))
        self.back_button.setStyleSheet(nav_button_style)
        self.search_bar_layout.addWidget(self.back_button)

        self.forward_button = QPushButton(">", self.central_widget)
        self.forward_button.setObjectName("forwardButton")
        self.forward_button.setMinimumSize(QSize(0, 32))
        self.forward_button.setMaximumSize(QSize(32, 16777215))
        self.forward_button.setStyleSheet(nav_button_style)
        self.search_bar_layout.addWidget(self.forward_button)

        self.search_field = QLineEdit(self.central_widget)
        self.search_field.setPlaceholderText(Translations["home.search_entries"])
        self.search_field.setObjectName("searchField")
        self.search_field.setMinimumSize(QSize(0, 32))
        self.search_field_completion_list = QStringListModel()
        self.search_field_completer = QCompleter(
            self.search_field_completion_list, self.search_field
        )
        self.search_field_completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.search_field.setCompleter(self.search_field_completer)
        self.search_bar_layout.addWidget(self.search_field)

        self.search_button = QPushButton(Translations["home.search"], self.central_widget)
        self.search_button.setObjectName("searchButton")
        self.search_button.setMinimumSize(QSize(0, 32))
        self.search_bar_layout.addWidget(self.search_button)

        self.central_layout.addLayout(self.search_bar_layout, 3, 0, 1, 1)
        # endregion

        # region Extra Input Bar:   Inputs for Sorting Settings and Thumbnail Size
        self.extra_input_layout = QHBoxLayout()
        self.extra_input_layout.setObjectName("extra_input_layout")

        ## left side spacer
        self.extra_input_layout.addItem(
            QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        )

        ## Sorting Dropdowns
        self.sorting_mode_combobox = QComboBox(self.central_widget)
        self.sorting_mode_combobox.setObjectName("sortingModeComboBox")
        self.extra_input_layout.addWidget(self.sorting_mode_combobox)

        self.sorting_direction_combobox = QComboBox(self.central_widget)
        self.sorting_direction_combobox.setObjectName("sortingDirectionCombobox")
        self.extra_input_layout.addWidget(self.sorting_direction_combobox)

        ## Thumbnail Size placeholder
        self.thumb_size_combobox = QComboBox(self.central_widget)
        self.thumb_size_combobox.setObjectName("thumbSizeComboBox")
        self.thumb_size_combobox.setPlaceholderText(Translations["home.thumbnail_size"])
        self.thumb_size_combobox.setCurrentText("")
        size_policy = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        size_policy.setHorizontalStretch(0)
        size_policy.setVerticalStretch(0)
        size_policy.setHeightForWidth(self.thumb_size_combobox.sizePolicy().hasHeightForWidth())
        self.thumb_size_combobox.setSizePolicy(size_policy)
        self.thumb_size_combobox.setMinimumWidth(128)
        self.thumb_size_combobox.setMaximumWidth(352)
        self.extra_input_layout.addWidget(self.thumb_size_combobox)

        self.central_layout.addLayout(self.extra_input_layout, 5, 0, 1, 1)
        # endregion

        # region Content: Entry Scroll List
        self.content_layout = QHBoxLayout()
        self.content_layout.setObjectName("horizontalLayout")

        self.content_splitter = QSplitter()
        self.content_splitter.setObjectName("splitter")
        self.content_splitter.setHandleWidth(12)

        # region Entry List
        self.entry_list_container = QWidget()
        self.entry_list_layout = QVBoxLayout(self.entry_list_container)
        self.entry_list_layout.setSpacing(0)

        self.entry_scroll_area = QScrollArea()
        self.entry_scroll_area.setObjectName("scrollArea")
        self.entry_scroll_area.setFocusPolicy(Qt.FocusPolicy.WheelFocus)
        self.entry_scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.entry_scroll_area.setFrameShadow(QFrame.Shadow.Plain)
        self.entry_scroll_area.setWidgetResizable(True)
        self.entry_list_layout.addWidget(self.entry_scroll_area)

        self.landing_widget: LandingWidget = LandingWidget(driver, self.devicePixelRatio())
        self.entry_list_layout.addWidget(self.landing_widget)

        self.pagination = Pagination()
        self.entry_list_layout.addWidget(self.pagination)
        # endregion

        self.content_splitter.addWidget(self.entry_list_container)
        self.content_splitter.setStretchFactor(0, 1)
        self.content_layout.addWidget(self.content_splitter)

        self.central_layout.addLayout(self.content_layout, 10, 0, 1, 1)
        # endregion

        self.setCentralWidget(self.central_widget)
        # endregion

        # region Status Bar
        self.status_bar = QStatusBar(self)
        self.status_bar.setObjectName("statusbar")
        status_bar_size_policy = QSizePolicy(
            QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum
        )
        status_bar_size_policy.setHorizontalStretch(0)
        status_bar_size_policy.setVerticalStretch(0)
        status_bar_size_policy.setHeightForWidth(self.status_bar.sizePolicy().hasHeightForWidth())
        self.status_bar.setSizePolicy(status_bar_size_policy)
        self.status_bar.setSizeGripEnabled(False)
        self.setStatusBar(self.status_bar)
        # endregion

        QMetaObject.connectSlotsByName(self)

        # NOTE: These are old attempts to allow for a translucent/acrylic
        # window effect. This may be attempted again in the future.
        # self.setWindowFlag(Qt.WindowType.NoDropShadowWindowHint, True)
        # self.setWindowFlag(Qt.WindowType.WindowTransparentForInput, False)
        # # self.setWindowFlag(Qt.WindowType.FramelessWindowHint, True)
        # self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # self.windowFX = WindowEffect()
        # self.windowFX.setAcrylicEffect(self.winId(), isEnableShadow=False)

    def moveEvent(self, event) -> None:  # noqa: N802
        # time.sleep(0.02)  # sleep for 20ms
        pass

    def resizeEvent(self, event) -> None:  # noqa: N802
        # time.sleep(0.02)  # sleep for 20ms
        pass

    def toggle_landing_page(self, enabled: bool):
        if enabled:
            self.entry_scroll_area.setHidden(True)
            self.landing_widget.setHidden(False)
            self.landing_widget.animate_logo_in()
        else:
            self.landing_widget.setHidden(True)
            self.landing_widget.set_status_label("")
            self.entry_scroll_area.setHidden(False)
