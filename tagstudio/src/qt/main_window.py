# Copyright (C) 2025 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio


import logging
import typing
from PySide6.QtCore import (QCoreApplication, QMetaObject, QRect,QSize, Qt, QStringListModel)
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (QComboBox, QFrame, QGridLayout,
                               QHBoxLayout, QVBoxLayout, QLayout, QLineEdit, QMainWindow,
                               QPushButton, QScrollArea, QSizePolicy,
                               QStatusBar, QWidget, QSplitter, QCheckBox,
                               QSpacerItem, QCompleter)
from src.qt.pagination import Pagination
from src.qt.widgets.landing import LandingWidget

from src.qt.translations import Translations

# Only import for type checking/autocompletion, will not be imported at runtime.
if typing.TYPE_CHECKING:
    from src.qt.ts_qt import QtDriver

logging.basicConfig(format="%(message)s", level=logging.INFO)


class Ui_MainWindow(QMainWindow):
  
    def __init__(self, driver: "QtDriver", parent=None) -> None:
        super().__init__(parent)
        self.driver: "QtDriver" = driver
        self.setupUi(self)

        # NOTE: These are old attempts to allow for a translucent/acrylic
        # window effect. This may be attempted again in the future.
        # self.setWindowFlag(Qt.WindowType.NoDropShadowWindowHint, True)
        # self.setWindowFlag(Qt.WindowType.WindowTransparentForInput, False)
        # # self.setWindowFlag(Qt.WindowType.FramelessWindowHint, True)
        # self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # self.windowFX = WindowEffect()
        # self.windowFX.setAcrylicEffect(self.winId(), isEnableShadow=False)


    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(1300, 720)
        
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.gridLayout = QGridLayout(self.centralwidget)
        self.gridLayout.setObjectName(u"gridLayout")
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
  
        # ComboBox group for search type and thumbnail size
        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
  
        # left side spacer
        spacerItem = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.horizontalLayout_3.addItem(spacerItem)
  
        # Sorting Dropdowns
        self.sorting_mode_combobox = QComboBox(self.centralwidget)
        self.sorting_mode_combobox.setObjectName(u"sortingModeComboBox")
        self.horizontalLayout_3.addWidget(self.sorting_mode_combobox)
        
        self.sorting_direction_combobox = QComboBox(self.centralwidget)
        self.sorting_direction_combobox.setObjectName(u"sortingDirectionCombobox")
        self.horizontalLayout_3.addWidget(self.sorting_direction_combobox)

        # Thumbnail Size placeholder
        self.thumb_size_combobox = QComboBox(self.centralwidget)
        self.thumb_size_combobox.setObjectName(u"thumbSizeComboBox")
        self.thumb_size_combobox.setPlaceholderText(Translations["home.thumbnail_size"])
        self.thumb_size_combobox.setCurrentText("")
        sizePolicy = QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(
            self.thumb_size_combobox.sizePolicy().hasHeightForWidth())
        self.thumb_size_combobox.setSizePolicy(sizePolicy)
        self.thumb_size_combobox.setMinimumWidth(128)
        self.thumb_size_combobox.setMaximumWidth(352)
        self.horizontalLayout_3.addWidget(self.thumb_size_combobox)
        self.gridLayout.addLayout(self.horizontalLayout_3, 5, 0, 1, 1)

        self.splitter = QSplitter()
        self.splitter.setObjectName(u"splitter")
        self.splitter.setHandleWidth(12)

        self.frame_container = QWidget()
        self.frame_layout = QVBoxLayout(self.frame_container)
        self.frame_layout.setSpacing(0)

        self.scrollArea = QScrollArea()
        self.scrollArea.setObjectName(u"scrollArea")
        self.scrollArea.setFocusPolicy(Qt.WheelFocus)
        self.scrollArea.setFrameShape(QFrame.NoFrame)
        self.scrollArea.setFrameShadow(QFrame.Plain)
        self.scrollArea.setWidgetResizable(True)
        self.scrollAreaWidgetContents = QWidget()
        self.scrollAreaWidgetContents.setObjectName(
            u"scrollAreaWidgetContents")
        self.scrollAreaWidgetContents.setGeometry(QRect(0, 0, 1260, 590))
        self.gridLayout_2 = QGridLayout(self.scrollAreaWidgetContents)
        self.gridLayout_2.setSpacing(8)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.gridLayout_2.setContentsMargins(0, 0, 0, 8)
        self.scrollArea.setWidget(self.scrollAreaWidgetContents)
        self.frame_layout.addWidget(self.scrollArea)
        
        self.landing_widget: LandingWidget = LandingWidget(self.driver, self.devicePixelRatio())
        self.frame_layout.addWidget(self.landing_widget)

        self.pagination = Pagination()
        self.frame_layout.addWidget(self.pagination)

        self.horizontalLayout.addWidget(self.splitter)
        self.splitter.addWidget(self.frame_container)
        self.splitter.setStretchFactor(0, 1)
        self.gridLayout.addLayout(self.horizontalLayout, 10, 0, 1, 1)

        nav_button_style = "font-size:14;font-weight:bold;"
        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setSizeConstraint(QLayout.SetMinimumSize)
        self.backButton = QPushButton("<", self.centralwidget)
        self.backButton.setObjectName(u"backButton")
        self.backButton.setMinimumSize(QSize(0, 32))
        self.backButton.setMaximumSize(QSize(32, 16777215))
        self.backButton.setStyleSheet(nav_button_style)
        self.horizontalLayout_2.addWidget(self.backButton)

        self.forwardButton = QPushButton(">", self.centralwidget)
        self.forwardButton.setObjectName(u"forwardButton")
        self.forwardButton.setMinimumSize(QSize(0, 32))
        self.forwardButton.setMaximumSize(QSize(32, 16777215))
        self.forwardButton.setStyleSheet(nav_button_style)
        self.horizontalLayout_2.addWidget(self.forwardButton)

        self.searchField = QLineEdit(self.centralwidget)
        self.searchField.setPlaceholderText(Translations["home.search_entries"])
        self.searchField.setObjectName(u"searchField")
        self.searchField.setMinimumSize(QSize(0, 32))

        self.searchFieldCompletionList = QStringListModel()
        self.searchFieldCompleter = QCompleter(self.searchFieldCompletionList, self.searchField)
        self.searchFieldCompleter.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.searchField.setCompleter(self.searchFieldCompleter)
        self.horizontalLayout_2.addWidget(self.searchField)

        self.searchButton = QPushButton(Translations["home.search"], self.centralwidget)
        self.searchButton.setObjectName(u"searchButton")
        self.searchButton.setMinimumSize(QSize(0, 32))

        self.horizontalLayout_2.addWidget(self.searchButton)
        self.gridLayout.addLayout(self.horizontalLayout_2, 3, 0, 1, 1)
        self.gridLayout_2.setContentsMargins(6, 6, 6, 6)

        MainWindow.setCentralWidget(self.centralwidget)
        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName(u"statusbar")
        sizePolicy1 = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(
            self.statusbar.sizePolicy().hasHeightForWidth())
        self.statusbar.setSizePolicy(sizePolicy1)
        self.statusbar.setSizeGripEnabled(False)
        MainWindow.setStatusBar(self.statusbar)

        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def moveEvent(self, event) -> None:
        # time.sleep(0.02)  # sleep for 20ms
        pass

    def resizeEvent(self, event) -> None:
        # time.sleep(0.02)  # sleep for 20ms
        pass

    def toggle_landing_page(self, enabled: bool):
        if enabled:
            self.scrollArea.setHidden(True)
            self.landing_widget.setHidden(False)
            self.landing_widget.animate_logo_in()
        else:
            self.landing_widget.setHidden(True)
            self.landing_widget.set_status_label("")
            self.scrollArea.setHidden(False)
            