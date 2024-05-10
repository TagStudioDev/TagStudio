# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'settings.ui'
##
## Created by: Qt User Interface Compiler version 6.5.1
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (
    QCoreApplication,
    QDate,
    QDateTime,
    QLocale,
    QMetaObject,
    QObject,
    QPoint,
    QRect,
    QSize,
    QTime,
    QUrl,
    Qt,
)
from PySide6.QtGui import (
    QBrush,
    QColor,
    QConicalGradient,
    QCursor,
    QFont,
    QFontDatabase,
    QGradient,
    QIcon,
    QImage,
    QKeySequence,
    QLinearGradient,
    QPainter,
    QPalette,
    QPixmap,
    QRadialGradient,
    QTransform,
)
from PySide6.QtWidgets import (
    QAbstractButton,
    QAbstractScrollArea,
    QApplication,
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFrame,
    QGridLayout,
    QLabel,
    QLayout,
    QScrollArea,
    QSizePolicy,
    QSpacerItem,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)


class Ui_Settings(object):
    def setupUi(self, Settings):
        if not Settings.objectName():
            Settings.setObjectName("Settings")
        Settings.setWindowModality(Qt.WindowModal)
        Settings.resize(400, 300)
        sizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(Settings.sizePolicy().hasHeightForWidth())
        Settings.setSizePolicy(sizePolicy)
        Settings.setMinimumSize(QSize(400, 300))
        Settings.setSizeGripEnabled(True)
        Settings.setModal(True)
        Settings.setProperty("autosave_interval", 5)
        self.verticalLayout = QVBoxLayout(Settings)
        self.verticalLayout.setObjectName("verticalLayout")
        self.tabWidget = QTabWidget(Settings)
        self.tabWidget.setObjectName("tabWidget")
        sizePolicy1 = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.tabWidget.sizePolicy().hasHeightForWidth())
        self.tabWidget.setSizePolicy(sizePolicy1)
        self.tabWidget.setUsesScrollButtons(False)
        self.tab = QWidget()
        self.tab.setObjectName("tab")
        self.verticalLayout_3 = QVBoxLayout(self.tab)
        self.verticalLayout_3.setSpacing(0)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.verticalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.scrollArea = QScrollArea(self.tab)
        self.scrollArea.setObjectName("scrollArea")
        self.scrollArea.setFrameShape(QFrame.NoFrame)
        self.scrollArea.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scrollArea.setSizeAdjustPolicy(QAbstractScrollArea.AdjustToContents)
        self.scrollArea.setWidgetResizable(True)
        self.scrollAreaWidgetContents = QWidget()
        self.scrollAreaWidgetContents.setObjectName("scrollAreaWidgetContents")
        self.scrollAreaWidgetContents.setGeometry(QRect(0, 0, 376, 223))
        sizePolicy2 = QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(
            self.scrollAreaWidgetContents.sizePolicy().hasHeightForWidth()
        )
        self.scrollAreaWidgetContents.setSizePolicy(sizePolicy2)
        self.verticalLayout_2 = QVBoxLayout(self.scrollAreaWidgetContents)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.verticalLayout_2.setSizeConstraint(QLayout.SetMinimumSize)
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.general_tab = QGridLayout()
        self.general_tab.setObjectName("general_tab")
        self.general_tab.setSizeConstraint(QLayout.SetMinimumSize)
        self.general_tab.setHorizontalSpacing(6)
        self.general_tab.setContentsMargins(6, 6, -1, -1)
        self.label = QLabel(self.scrollAreaWidgetContents)
        self.label.setObjectName("label")
        sizePolicy2.setHeightForWidth(self.label.sizePolicy().hasHeightForWidth())
        self.label.setSizePolicy(sizePolicy2)
        font = QFont()
        font.setPointSize(15)
        font.setBold(True)
        font.setItalic(True)
        self.label.setFont(font)

        self.general_tab.addWidget(self.label, 0, 0, 1, 1)

        self.verticalSpacer = QSpacerItem(
            20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding
        )

        self.general_tab.addItem(self.verticalSpacer, 3, 0, 1, 1)

        self.autosave_interval = QSpinBox(self.scrollAreaWidgetContents)
        self.autosave_interval.setObjectName("autosave_interval")
        sizePolicy2.setHeightForWidth(
            self.autosave_interval.sizePolicy().hasHeightForWidth()
        )
        self.autosave_interval.setSizePolicy(sizePolicy2)
        self.autosave_interval.setMinimum(5)
        self.autosave_interval.setMaximum(60)
        self.autosave_interval.setSingleStep(5)

        self.general_tab.addWidget(self.autosave_interval, 2, 1, 1, 1)

        self.horizontalSpacer = QSpacerItem(
            40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum
        )

        self.general_tab.addItem(self.horizontalSpacer, 0, 2, 1, 1)

        self.label_2 = QLabel(self.scrollAreaWidgetContents)
        self.label_2.setObjectName("label_2")
        sizePolicy2.setHeightForWidth(self.label_2.sizePolicy().hasHeightForWidth())
        self.label_2.setSizePolicy(sizePolicy2)
        self.label_2.setLayoutDirection(Qt.LeftToRight)
        self.label_2.setAlignment(Qt.AlignRight | Qt.AlignTrailing | Qt.AlignVCenter)

        self.general_tab.addWidget(self.label_2, 2, 0, 1, 1)

        self.autosave_toggle = QCheckBox(self.scrollAreaWidgetContents)
        self.autosave_toggle.setObjectName("autosave_toggle")
        sizePolicy2.setHeightForWidth(
            self.autosave_toggle.sizePolicy().hasHeightForWidth()
        )
        self.autosave_toggle.setSizePolicy(sizePolicy2)
        self.autosave_toggle.setChecked(True)

        self.general_tab.addWidget(self.autosave_toggle, 1, 0, 1, 2)

        self.verticalLayout_2.addLayout(self.general_tab)

        self.scrollArea.setWidget(self.scrollAreaWidgetContents)

        self.verticalLayout_3.addWidget(self.scrollArea)

        self.tabWidget.addTab(self.tab, "")
        self.tab_2 = QWidget()
        self.tab_2.setObjectName("tab_2")
        self.verticalLayout_4 = QVBoxLayout(self.tab_2)
        self.verticalLayout_4.setObjectName("verticalLayout_4")
        self.verticalLayout_4.setContentsMargins(0, 0, 0, 0)
        self.scrollArea_2 = QScrollArea(self.tab_2)
        self.scrollArea_2.setObjectName("scrollArea_2")
        self.scrollArea_2.setFrameShape(QFrame.NoFrame)
        self.scrollArea_2.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scrollArea_2.setSizeAdjustPolicy(QAbstractScrollArea.AdjustToContents)
        self.scrollArea_2.setWidgetResizable(True)
        self.scrollAreaWidgetContents_4 = QWidget()
        self.scrollAreaWidgetContents_4.setObjectName("scrollAreaWidgetContents_4")
        self.scrollAreaWidgetContents_4.setGeometry(QRect(0, 0, 376, 223))
        sizePolicy2.setHeightForWidth(
            self.scrollAreaWidgetContents_4.sizePolicy().hasHeightForWidth()
        )
        self.scrollAreaWidgetContents_4.setSizePolicy(sizePolicy2)
        self.verticalLayout_5 = QVBoxLayout(self.scrollAreaWidgetContents_4)
        self.verticalLayout_5.setObjectName("verticalLayout_5")
        self.verticalLayout_5.setSizeConstraint(QLayout.SetMinimumSize)
        self.verticalLayout_5.setContentsMargins(0, 0, 0, 0)
        self.general_tab_3 = QGridLayout()
        self.general_tab_3.setObjectName("general_tab_3")
        self.general_tab_3.setSizeConstraint(QLayout.SetMinimumSize)
        self.general_tab_3.setHorizontalSpacing(6)
        self.general_tab_3.setContentsMargins(6, 6, -1, -1)
        self.render_thumbnails = QCheckBox(self.scrollAreaWidgetContents_4)
        self.render_thumbnails.setObjectName("render_thumbnails")
        sizePolicy2.setHeightForWidth(
            self.render_thumbnails.sizePolicy().hasHeightForWidth()
        )
        self.render_thumbnails.setSizePolicy(sizePolicy2)
        self.render_thumbnails.setChecked(False)

        self.general_tab_3.addWidget(self.render_thumbnails, 1, 0, 1, 1)

        self.checkBox = QCheckBox(self.scrollAreaWidgetContents_4)
        self.checkBox.setObjectName("checkBox")

        self.general_tab_3.addWidget(self.checkBox, 2, 0, 1, 1)

        self.spinBox = QSpinBox(self.scrollAreaWidgetContents_4)
        self.spinBox.setObjectName("spinBox")
        self.spinBox.setEnabled(False)
        self.spinBox.setMinimumSize(QSize(100, 0))
        self.spinBox.setMinimum(4)
        self.spinBox.setMaximum(100)

        self.general_tab_3.addWidget(self.spinBox, 3, 1, 1, 1)

        self.label_5 = QLabel(self.scrollAreaWidgetContents_4)
        self.label_5.setObjectName("label_5")
        sizePolicy2.setHeightForWidth(self.label_5.sizePolicy().hasHeightForWidth())
        self.label_5.setSizePolicy(sizePolicy2)
        self.label_5.setFont(font)

        self.general_tab_3.addWidget(self.label_5, 0, 0, 1, 1)

        self.label_3 = QLabel(self.scrollAreaWidgetContents_4)
        self.label_3.setObjectName("label_3")
        self.label_3.setEnabled(True)
        self.label_3.setAlignment(Qt.AlignRight | Qt.AlignTrailing | Qt.AlignVCenter)

        self.general_tab_3.addWidget(self.label_3, 3, 0, 1, 1)

        self.verticalSpacer_3 = QSpacerItem(
            20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding
        )

        self.general_tab_3.addItem(self.verticalSpacer_3, 4, 0, 1, 1)

        self.horizontalSpacer_3 = QSpacerItem(
            40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum
        )

        self.general_tab_3.addItem(self.horizontalSpacer_3, 1, 2, 1, 1)

        self.verticalLayout_5.addLayout(self.general_tab_3)

        self.scrollArea_2.setWidget(self.scrollAreaWidgetContents_4)

        self.verticalLayout_4.addWidget(self.scrollArea_2)

        self.tabWidget.addTab(self.tab_2, "")

        self.verticalLayout.addWidget(self.tabWidget)

        self.buttonBox = QDialogButtonBox(Settings)
        self.buttonBox.setObjectName("buttonBox")
        self.buttonBox.setOrientation(Qt.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Cancel | QDialogButtonBox.Ok)

        self.verticalLayout.addWidget(self.buttonBox)

        # if QT_CONFIG(shortcut)
        self.label_2.setBuddy(self.autosave_interval)
        self.label_3.setBuddy(self.spinBox)
        # endif // QT_CONFIG(shortcut)

        self.retranslateUi(Settings)
        self.buttonBox.accepted.connect(Settings.accept)
        self.buttonBox.rejected.connect(Settings.reject)
        self.autosave_toggle.toggled.connect(self.autosave_interval.setEnabled)
        self.checkBox.toggled.connect(self.spinBox.setEnabled)
        self.render_thumbnails.toggled.connect(self.checkBox.setDisabled)

        self.tabWidget.setCurrentIndex(1)

        QMetaObject.connectSlotsByName(Settings)

    # setupUi

    def retranslateUi(self, Settings):
        Settings.setWindowTitle(
            QCoreApplication.translate("Settings", "Settings", None)
        )
        self.label.setText(
            QCoreApplication.translate("Settings", "Saving/Loading", None)
        )
        self.autosave_interval.setSuffix(
            QCoreApplication.translate("Settings", " minutes", None)
        )
        self.label_2.setText(
            QCoreApplication.translate("Settings", "Autosave Interval", None)
        )
        self.autosave_toggle.setText(
            QCoreApplication.translate("Settings", "Autosave", None)
        )
        self.tabWidget.setTabText(
            self.tabWidget.indexOf(self.tab),
            QCoreApplication.translate("Settings", "General", None),
        )
        self.render_thumbnails.setText(
            QCoreApplication.translate("Settings", "Do not render thumbnails.", None)
        )
        self.checkBox.setText(
            QCoreApplication.translate("Settings", "Limit Thumbnail Threads", None)
        )
        self.label_5.setText(QCoreApplication.translate("Settings", "Mainview", None))
        self.label_3.setText(
            QCoreApplication.translate("Settings", "Thread Count", None)
        )
        self.tabWidget.setTabText(
            self.tabWidget.indexOf(self.tab_2),
            QCoreApplication.translate("Settings", "Performance", None),
        )

    # retranslateUi
