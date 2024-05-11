# -*- coding: utf-8 -*-

################################################################################
# Form generated from reading UI file 'home.ui'
##
# Created by: Qt User Interface Compiler version 6.5.1
##
# WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

# Copyright (C) 2024 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio

from PySide6.QtCore import (QCoreApplication, QMetaObject, QRect,
							QSize, Qt)
from PySide6.QtGui import (QFont, QAction)
from PySide6.QtWidgets import (QComboBox, QFrame, QGridLayout,
							   QHBoxLayout, QVBoxLayout, QLayout, QLineEdit, QMainWindow,
							   QMenuBar, QPushButton, QScrollArea, QSizePolicy,
							   QStatusBar, QWidget, QSplitter, QMenu)
from src.qt.pagination import Pagination


class Ui_MainWindow(QMainWindow):
	def __init__(self, parent=None) -> None:
		super().__init__(parent)
		self.setupUi(self)

		# self.setWindowFlag(Qt.WindowType.NoDropShadowWindowHint, True)
		# self.setWindowFlag(Qt.WindowType.WindowTransparentForInput, False)
		# # self.setWindowFlag(Qt.WindowType.FramelessWindowHint, True)
		# self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

		# self.windowFX = WindowEffect()
		# self.windowFX.setAcrylicEffect(self.winId(), isEnableShadow=False)

		# # self.setStyleSheet(
		# # 	'background:#EE000000;'
		# # 	)
		

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

		# self.page_bar_controls = QWidget()
		# self.page_bar_controls.setStyleSheet('background:blue;')
		# self.page_bar_controls.setMinimumHeight(32)

		self.pagination = Pagination()
		self.frame_layout.addWidget(self.pagination)

		# self.frame_layout.addWidget(self.page_bar_controls)
		# self.frame_layout.addWidget(self.page_bar_controls)

		self.horizontalLayout.addWidget(self.splitter)
		self.splitter.addWidget(self.frame_container)
		self.splitter.setStretchFactor(0, 1)

		self.gridLayout.addLayout(self.horizontalLayout, 10, 0, 1, 1)

		self.horizontalLayout_2 = QHBoxLayout()
		self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
		self.horizontalLayout_2.setSizeConstraint(QLayout.SetMinimumSize)
		self.backButton = QPushButton(self.centralwidget)
		self.backButton.setObjectName(u"backButton")
		self.backButton.setMinimumSize(QSize(0, 32))
		self.backButton.setMaximumSize(QSize(32, 16777215))
		font = QFont()
		font.setPointSize(14)
		font.setBold(True)
		self.backButton.setFont(font)

		self.horizontalLayout_2.addWidget(self.backButton)

		self.forwardButton = QPushButton(self.centralwidget)
		self.forwardButton.setObjectName(u"forwardButton")
		self.forwardButton.setMinimumSize(QSize(0, 32))
		self.forwardButton.setMaximumSize(QSize(32, 16777215))
		font1 = QFont()
		font1.setPointSize(14)
		font1.setBold(True)
		font1.setKerning(True)
		self.forwardButton.setFont(font1)

		self.horizontalLayout_2.addWidget(self.forwardButton)

		self.searchField = QLineEdit(self.centralwidget)
		self.searchField.setObjectName(u"searchField")
		self.searchField.setMinimumSize(QSize(0, 32))
		font2 = QFont()
		font2.setPointSize(11)
		font2.setBold(False)
		self.searchField.setFont(font2)

		self.horizontalLayout_2.addWidget(self.searchField)

		self.searchButton = QPushButton(self.centralwidget)
		self.searchButton.setObjectName(u"searchButton")
		self.searchButton.setMinimumSize(QSize(0, 32))
		self.searchButton.setFont(font2)

		self.horizontalLayout_2.addWidget(self.searchButton)
		self.gridLayout.addLayout(self.horizontalLayout_2, 3, 0, 1, 1)

		self.comboBox = QComboBox(self.centralwidget)
		self.comboBox.setObjectName(u"comboBox")
		sizePolicy = QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
		sizePolicy.setHorizontalStretch(0)
		sizePolicy.setVerticalStretch(0)
		sizePolicy.setHeightForWidth(
			self.comboBox.sizePolicy().hasHeightForWidth())
		self.comboBox.setSizePolicy(sizePolicy)
		self.comboBox.setMinimumWidth(128)
		self.comboBox.setMaximumWidth(128)

		self.gridLayout.addWidget(self.comboBox, 4, 0, 1, 1, Qt.AlignRight)

		self.gridLayout_2.setContentsMargins(6, 6, 6, 6)

		MainWindow.setCentralWidget(self.centralwidget)
		# self.menubar = QMenuBar(MainWindow)
		# self.menubar.setObjectName(u"menubar")
		# self.menubar.setGeometry(QRect(0, 0, 1280, 22))
		# MainWindow.setMenuBar(self.menubar)
		self.statusbar = QStatusBar(MainWindow)
		self.statusbar.setObjectName(u"statusbar")
		sizePolicy1 = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
		sizePolicy1.setHorizontalStretch(0)
		sizePolicy1.setVerticalStretch(0)
		sizePolicy1.setHeightForWidth(
			self.statusbar.sizePolicy().hasHeightForWidth())
		self.statusbar.setSizePolicy(sizePolicy1)
		MainWindow.setStatusBar(self.statusbar)

		menu_bar = self.menuBar()
		self.setMenuBar(menu_bar)
		# self.gridLayout.addWidget(menu_bar, 4, 0, 1, 1, Qt.AlignRight)
		self.frame_layout.addWidget(menu_bar)

		self.retranslateUi(MainWindow)

		QMetaObject.connectSlotsByName(MainWindow)
	# setupUi

	def retranslateUi(self, MainWindow):
		MainWindow.setWindowTitle(QCoreApplication.translate(
			"MainWindow", u"MainWindow", None))
		self.backButton.setText(
			QCoreApplication.translate("MainWindow", u"<", None))
		self.forwardButton.setText(
			QCoreApplication.translate("MainWindow", u">", None))
		self.searchField.setPlaceholderText(
			QCoreApplication.translate("MainWindow", u"Search Entries", None))
		self.searchButton.setText(
			QCoreApplication.translate("MainWindow", u"Search", None))
		self.comboBox.setCurrentText("")
		self.comboBox.setPlaceholderText(
			QCoreApplication.translate("MainWindow", u"Thumbnail Size", None))
	# retranslateUi

	def moveEvent(self, event) -> None:
		# time.sleep(0.02)  # sleep for 20ms
		pass

	def resizeEvent(self, event) -> None:
		# time.sleep(0.02)  # sleep for 20ms
		pass

	def _createMenuBar(self, main_window):
		menu_bar = QMenuBar(main_window)
		file_menu = QMenu('&File', main_window)
		edit_menu = QMenu('&Edit', main_window)
		tools_menu = QMenu('&Tools', main_window)
		macros_menu = QMenu('&Macros', main_window)
		help_menu = QMenu('&Help', main_window)

		file_menu.addAction(QAction('&New Library', main_window))
		file_menu.addAction(QAction('&Open Library', main_window))
		file_menu.addAction(QAction('&Save Library', main_window))
		file_menu.addAction(QAction('&Close Library', main_window))

		file_menu.addAction(QAction('&Refresh Directories', main_window))
		file_menu.addAction(QAction('&Add New Files to Library', main_window))

		menu_bar.addMenu(file_menu)
		menu_bar.addMenu(edit_menu)
		menu_bar.addMenu(tools_menu)
		menu_bar.addMenu(macros_menu)
		menu_bar.addMenu(help_menu)

		main_window.setMenuBar(menu_bar)
