# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'home.ui'
##
## Created by: Qt User Interface Compiler version 6.5.1
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import QCoreApplication, QMetaObject, QRect, QSize, Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (QComboBox, QFrame, QGridLayout, QHBoxLayout,
    QLayout, QLineEdit, QMenuBar, QPushButton, QScrollArea, QSizePolicy,
    QStatusBar, QWidget)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(1280, 720)
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.gridLayout = QGridLayout(self.centralwidget)
        self.gridLayout.setObjectName(u"gridLayout")
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.scrollArea = QScrollArea(self.centralwidget)
        self.scrollArea.setObjectName(u"scrollArea")
        self.scrollArea.setFocusPolicy(Qt.WheelFocus)
        self.scrollArea.setFrameShape(QFrame.NoFrame)
        self.scrollArea.setFrameShadow(QFrame.Plain)
        self.scrollArea.setWidgetResizable(True)
        self.scrollAreaWidgetContents = QWidget()
        self.scrollAreaWidgetContents.setObjectName(u"scrollAreaWidgetContents")
        self.scrollAreaWidgetContents.setGeometry(QRect(0, 0, 1260, 590))
        self.gridLayout_2 = QGridLayout(self.scrollAreaWidgetContents)
        self.gridLayout_2.setSpacing(8)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.gridLayout_2.setContentsMargins(0, 0, 0, 8)
        self.scrollArea.setWidget(self.scrollAreaWidgetContents)

        self.horizontalLayout.addWidget(self.scrollArea)


        self.gridLayout.addLayout(self.horizontalLayout, 5, 0, 1, 1)

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
        sizePolicy.setHeightForWidth(self.comboBox.sizePolicy().hasHeightForWidth())
        self.comboBox.setSizePolicy(sizePolicy)
        self.comboBox.setMinimumSize(QSize(128, 0))
        self.comboBox.setMaximumSize(QSize(256, 32))

        self.gridLayout.addWidget(self.comboBox, 4, 0, 1, 1, Qt.AlignRight)

        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 1280, 22))
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName(u"statusbar")
        sizePolicy1 = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.statusbar.sizePolicy().hasHeightForWidth())
        self.statusbar.setSizePolicy(sizePolicy1)
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)

        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"MainWindow", None))
        self.backButton.setText(QCoreApplication.translate("MainWindow", u"<", None))
        self.forwardButton.setText(QCoreApplication.translate("MainWindow", u">", None))
        self.searchField.setPlaceholderText(QCoreApplication.translate("MainWindow", u"Search Entries", None))
        self.searchButton.setText(QCoreApplication.translate("MainWindow", u"Search", None))
        self.comboBox.setCurrentText("")
        self.comboBox.setPlaceholderText(QCoreApplication.translate("MainWindow", u"Thumbnail Size", None))
    # retranslateUi

