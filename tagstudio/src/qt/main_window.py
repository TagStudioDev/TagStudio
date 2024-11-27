# Copyright (C) 2024 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio


import typing

from PySide6.QtCore import QCoreApplication, QMetaObject, QRect, QSize, Qt, QStringListModel
from PySide6.QtGui import QFont
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
from src.qt.pagination import Pagination
from src.qt.widgets.landing import LandingWidget

# Only import for type checking/autocompletion, will not be imported at runtime.
if typing.TYPE_CHECKING:
    from src.qt.ts_qt import QtDriver


class UIMainWindow(QMainWindow):
    def __init__(self, driver: "QtDriver", parent=None) -> None:
        super().__init__(parent)
        self.driver: QtDriver = driver
        self._setup_ui()

        # NOTE: These are old attempts to allow for a translucent/acrylic
        # window effect. This may be attempted again in the future.
        # self.setWindowFlag(Qt.WindowType.NoDropShadowWindowHint, True)
        # self.setWindowFlag(Qt.WindowType.WindowTransparentForInput, False)
        # # self.setWindowFlag(Qt.WindowType.FramelessWindowHint, True)
        # self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # self.windowFX = WindowEffect()
        # self.windowFX.setAcrylicEffect(self.winId(), isEnableShadow=False)

        # # self.setStyleSheet(
        # # 	'background:#EE000000;'
        # # 	)

    def _setup_ui(self) -> None:
        if not self.objectName():
            self.setObjectName("MainWindow")
        self.resize(1300, 720)

        self.centralwidget = QWidget(self)
        self.centralwidget.setObjectName("centralwidget")
        self.gridLayout = QGridLayout(self.centralwidget)
        self.gridLayout.setObjectName("gridLayout")
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")

        # ComboBox group for search type and thumbnail size
        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")

        # left side spacer
        spacer_item = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self.horizontalLayout_3.addItem(spacer_item)

        # Thumbnail Size placeholder
        self.thumb_size_combobox = QComboBox(self.centralwidget)
        self.thumb_size_combobox.setObjectName("thumbSizeComboBox")
        size_policy = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        size_policy.setHorizontalStretch(0)
        size_policy.setVerticalStretch(0)
        size_policy.setHeightForWidth(self.thumb_size_combobox.sizePolicy().hasHeightForWidth())
        self.thumb_size_combobox.setSizePolicy(size_policy)
        self.thumb_size_combobox.setMinimumWidth(128)
        self.thumb_size_combobox.setMaximumWidth(352)
        self.horizontalLayout_3.addWidget(self.thumb_size_combobox)
        self.gridLayout.addLayout(self.horizontalLayout_3, 5, 0, 1, 1)

        self.splitter = QSplitter()
        self.splitter.setObjectName("splitter")
        self.splitter.setHandleWidth(12)

        self.frame_container = QWidget()
        self.frame_layout = QVBoxLayout(self.frame_container)
        self.frame_layout.setSpacing(0)

        self.scrollArea = QScrollArea()
        self.scrollArea.setObjectName("scrollArea")
        self.scrollArea.setFocusPolicy(Qt.FocusPolicy.WheelFocus)
        self.scrollArea.setFrameShape(QFrame.Shape.NoFrame)
        self.scrollArea.setFrameShadow(QFrame.Shadow.Plain)
        self.scrollArea.setWidgetResizable(True)
        self.scrollAreaWidgetContents = QWidget()
        self.scrollAreaWidgetContents.setObjectName("scrollAreaWidgetContents")
        self.scrollAreaWidgetContents.setGeometry(QRect(0, 0, 1260, 590))
        self.gridLayout_2 = QGridLayout(self.scrollAreaWidgetContents)
        self.gridLayout_2.setSpacing(8)
        self.gridLayout_2.setObjectName("gridLayout_2")
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

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.horizontalLayout_2.setSizeConstraint(QLayout.SizeConstraint.SetMinimumSize)
        self.backButton = QPushButton(self.centralwidget)
        self.backButton.setObjectName("backButton")
        self.backButton.setMinimumSize(QSize(0, 32))
        self.backButton.setMaximumSize(QSize(32, 16777215))
        font = QFont()
        font.setPointSize(14)
        font.setBold(True)
        self.backButton.setFont(font)

        self.horizontalLayout_2.addWidget(self.backButton)

        self.forwardButton = QPushButton(self.centralwidget)
        self.forwardButton.setObjectName("forwardButton")
        self.forwardButton.setMinimumSize(QSize(0, 32))
        self.forwardButton.setMaximumSize(QSize(32, 16777215))
        font1 = QFont()
        font1.setPointSize(14)
        font1.setBold(True)
        font1.setKerning(True)
        self.forwardButton.setFont(font1)

        self.horizontalLayout_2.addWidget(self.forwardButton)

        self.searchField = QLineEdit(self.centralwidget)
        self.searchField.setObjectName("searchField")
        self.searchField.setMinimumSize(QSize(0, 32))
        font2 = QFont()
        font2.setPointSize(11)
        font2.setBold(False)
        self.searchField.setFont(font2)

        self.searchFieldCompletionList = QStringListModel()
        self.searchFieldCompleter = QCompleter(self.searchFieldCompletionList, self.searchField)
        self.searchFieldCompleter.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.searchField.setCompleter(self.searchFieldCompleter)

        self.horizontalLayout_2.addWidget(self.searchField)

        self.searchButton = QPushButton(self.centralwidget)
        self.searchButton.setObjectName("searchButton")
        self.searchButton.setMinimumSize(QSize(0, 32))
        self.searchButton.setFont(font2)

        self.horizontalLayout_2.addWidget(self.searchButton)
        self.gridLayout.addLayout(self.horizontalLayout_2, 3, 0, 1, 1)
        self.gridLayout_2.setContentsMargins(6, 6, 6, 6)

        self.setCentralWidget(self.centralwidget)
        self.statusbar = QStatusBar(self)
        self.statusbar.setObjectName("statusbar")
        size_policy1 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        size_policy1.setHorizontalStretch(0)
        size_policy1.setVerticalStretch(0)
        size_policy1.setHeightForWidth(self.statusbar.sizePolicy().hasHeightForWidth())
        self.statusbar.setSizePolicy(size_policy1)
        self.setStatusBar(self.statusbar)

        self._retranslate_ui()

        QMetaObject.connectSlotsByName(self)

    def _retranslate_ui(self):
        self.setWindowTitle(QCoreApplication.translate("MainWindow", "MainWindow", None))
        # Navigation buttons
        self.backButton.setText(QCoreApplication.translate("MainWindow", "<", None))
        self.forwardButton.setText(QCoreApplication.translate("MainWindow", ">", None))

        # Search field
        self.searchField.setPlaceholderText(
            QCoreApplication.translate("MainWindow", "Search Entries", None)
        )
        self.searchButton.setText(QCoreApplication.translate("MainWindow", "Search", None))

        self.thumb_size_combobox.setCurrentText("")

        # Thumbnail size selector
        self.thumb_size_combobox.setPlaceholderText(
            QCoreApplication.translate("MainWindow", "Thumbnail Size", None)
        )

    def toggle_landing_page(self, enabled: bool):
        if enabled:
            self.scrollArea.setHidden(True)
            self.landing_widget.setHidden(False)
            self.landing_widget.animate_logo_in()
        else:
            self.landing_widget.setHidden(True)
            self.landing_widget.set_status_label("")
            self.scrollArea.setHidden(False)
