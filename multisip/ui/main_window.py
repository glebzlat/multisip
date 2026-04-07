# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'main_window.ui'
##
## Created by: Qt User Interface Compiler version 6.11.0
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QComboBox, QFormLayout, QGridLayout,
    QGroupBox, QHBoxLayout, QLabel, QMainWindow,
    QPlainTextEdit, QPushButton, QScrollArea, QSizePolicy,
    QSpacerItem, QTabWidget, QVBoxLayout, QWidget)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(709, 596)
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.gridLayout = QGridLayout(self.centralwidget)
        self.gridLayout.setObjectName(u"gridLayout")
        self.tabWidget = QTabWidget(self.centralwidget)
        self.tabWidget.setObjectName(u"tabWidget")
        self.userAgentsTab = QWidget()
        self.userAgentsTab.setObjectName(u"userAgentsTab")
        self.horizontalLayout = QHBoxLayout(self.userAgentsTab)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.userAgentsGroup = QGroupBox(self.userAgentsTab)
        self.userAgentsGroup.setObjectName(u"userAgentsGroup")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.userAgentsGroup.sizePolicy().hasHeightForWidth())
        self.userAgentsGroup.setSizePolicy(sizePolicy)
        self.gridLayout_2 = QGridLayout(self.userAgentsGroup)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.addUserAgentsButton = QPushButton(self.userAgentsGroup)
        self.addUserAgentsButton.setObjectName(u"addUserAgentsButton")

        self.gridLayout_2.addWidget(self.addUserAgentsButton, 0, 0, 1, 3)

        self.muteAllButton = QPushButton(self.userAgentsGroup)
        self.muteAllButton.setObjectName(u"muteAllButton")

        self.gridLayout_2.addWidget(self.muteAllButton, 1, 0, 1, 1)

        self.hangupAllButton = QPushButton(self.userAgentsGroup)
        self.hangupAllButton.setObjectName(u"hangupAllButton")

        self.gridLayout_2.addWidget(self.hangupAllButton, 1, 1, 1, 1)

        self.deleteAllButton = QPushButton(self.userAgentsGroup)
        self.deleteAllButton.setObjectName(u"deleteAllButton")

        self.gridLayout_2.addWidget(self.deleteAllButton, 1, 2, 1, 1)

        self.scrollArea = QScrollArea(self.userAgentsGroup)
        self.scrollArea.setObjectName(u"scrollArea")
        self.scrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scrollArea.setWidgetResizable(True)
        self.scrollAreaWidgetContents = QWidget()
        self.scrollAreaWidgetContents.setObjectName(u"scrollAreaWidgetContents")
        self.scrollAreaWidgetContents.setGeometry(QRect(0, 0, 306, 453))
        self.verticalLayout_3 = QVBoxLayout(self.scrollAreaWidgetContents)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.scrollArea.setWidget(self.scrollAreaWidgetContents)

        self.gridLayout_2.addWidget(self.scrollArea, 2, 0, 1, 3)


        self.horizontalLayout.addWidget(self.userAgentsGroup)

        self.userAgentSettingsGroup = QGroupBox(self.userAgentsTab)
        self.userAgentSettingsGroup.setObjectName(u"userAgentSettingsGroup")
        sizePolicy.setHeightForWidth(self.userAgentSettingsGroup.sizePolicy().hasHeightForWidth())
        self.userAgentSettingsGroup.setSizePolicy(sizePolicy)
        self.verticalLayout = QVBoxLayout(self.userAgentSettingsGroup)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.statusGroupBox = QGroupBox(self.userAgentSettingsGroup)
        self.statusGroupBox.setObjectName(u"statusGroupBox")
        self.formLayout = QFormLayout(self.statusGroupBox)
        self.formLayout.setObjectName(u"formLayout")
        self.userAgentStatusLabel = QLabel(self.statusGroupBox)
        self.userAgentStatusLabel.setObjectName(u"userAgentStatusLabel")

        self.formLayout.setWidget(0, QFormLayout.ItemRole.LabelRole, self.userAgentStatusLabel)

        self.userAgentStatusValue = QLabel(self.statusGroupBox)
        self.userAgentStatusValue.setObjectName(u"userAgentStatusValue")

        self.formLayout.setWidget(0, QFormLayout.ItemRole.FieldRole, self.userAgentStatusValue)

        self.userAgentUserLabel = QLabel(self.statusGroupBox)
        self.userAgentUserLabel.setObjectName(u"userAgentUserLabel")

        self.formLayout.setWidget(1, QFormLayout.ItemRole.LabelRole, self.userAgentUserLabel)

        self.userAgentUserValue = QLabel(self.statusGroupBox)
        self.userAgentUserValue.setObjectName(u"userAgentUserValue")

        self.formLayout.setWidget(1, QFormLayout.ItemRole.FieldRole, self.userAgentUserValue)

        self.userAgentDomainLabel = QLabel(self.statusGroupBox)
        self.userAgentDomainLabel.setObjectName(u"userAgentDomainLabel")

        self.formLayout.setWidget(2, QFormLayout.ItemRole.LabelRole, self.userAgentDomainLabel)

        self.userAgentDomainValue = QLabel(self.statusGroupBox)
        self.userAgentDomainValue.setObjectName(u"userAgentDomainValue")

        self.formLayout.setWidget(2, QFormLayout.ItemRole.FieldRole, self.userAgentDomainValue)


        self.verticalLayout.addWidget(self.statusGroupBox)

        self.deleteUAButton = QPushButton(self.userAgentSettingsGroup)
        self.deleteUAButton.setObjectName(u"deleteUAButton")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.deleteUAButton.sizePolicy().hasHeightForWidth())
        self.deleteUAButton.setSizePolicy(sizePolicy1)

        self.verticalLayout.addWidget(self.deleteUAButton)

        self.callGroupBox = QGroupBox(self.userAgentSettingsGroup)
        self.callGroupBox.setObjectName(u"callGroupBox")
        self.gridLayout_3 = QGridLayout(self.callGroupBox)
        self.gridLayout_3.setObjectName(u"gridLayout_3")
        self.callNumberLabel = QLabel(self.callGroupBox)
        self.callNumberLabel.setObjectName(u"callNumberLabel")

        self.gridLayout_3.addWidget(self.callNumberLabel, 0, 0, 1, 1)

        self.callNumberValue = QLabel(self.callGroupBox)
        self.callNumberValue.setObjectName(u"callNumberValue")

        self.gridLayout_3.addWidget(self.callNumberValue, 0, 1, 1, 1)

        self.muteUAButton = QPushButton(self.callGroupBox)
        self.muteUAButton.setObjectName(u"muteUAButton")
        sizePolicy1.setHeightForWidth(self.muteUAButton.sizePolicy().hasHeightForWidth())
        self.muteUAButton.setSizePolicy(sizePolicy1)

        self.gridLayout_3.addWidget(self.muteUAButton, 1, 0, 1, 1)

        self.hangupCallButton = QPushButton(self.callGroupBox)
        self.hangupCallButton.setObjectName(u"hangupCallButton")
        sizePolicy1.setHeightForWidth(self.hangupCallButton.sizePolicy().hasHeightForWidth())
        self.hangupCallButton.setSizePolicy(sizePolicy1)

        self.gridLayout_3.addWidget(self.hangupCallButton, 1, 1, 1, 1)


        self.verticalLayout.addWidget(self.callGroupBox)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer)


        self.horizontalLayout.addWidget(self.userAgentSettingsGroup)

        self.tabWidget.addTab(self.userAgentsTab, "")
        self.logsTab = QWidget()
        self.logsTab.setObjectName(u"logsTab")
        self.verticalLayout_2 = QVBoxLayout(self.logsTab)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.horizontalLayout_5 = QHBoxLayout()
        self.horizontalLayout_5.setObjectName(u"horizontalLayout_5")
        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.logLevelLabel = QLabel(self.logsTab)
        self.logLevelLabel.setObjectName(u"logLevelLabel")
        self.logLevelLabel.setLayoutDirection(Qt.LayoutDirection.LeftToRight)

        self.horizontalLayout_2.addWidget(self.logLevelLabel)

        self.logLevelSelector = QComboBox(self.logsTab)
        self.logLevelSelector.setObjectName(u"logLevelSelector")
        sizePolicy2 = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.logLevelSelector.sizePolicy().hasHeightForWidth())
        self.logLevelSelector.setSizePolicy(sizePolicy2)

        self.horizontalLayout_2.addWidget(self.logLevelSelector)

        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.displayLevelLabel = QLabel(self.logsTab)
        self.displayLevelLabel.setObjectName(u"displayLevelLabel")

        self.horizontalLayout_3.addWidget(self.displayLevelLabel)

        self.displayLevelSelector = QComboBox(self.logsTab)
        self.displayLevelSelector.setObjectName(u"displayLevelSelector")
        sizePolicy3 = QSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Fixed)
        sizePolicy3.setHorizontalStretch(0)
        sizePolicy3.setVerticalStretch(0)
        sizePolicy3.setHeightForWidth(self.displayLevelSelector.sizePolicy().hasHeightForWidth())
        self.displayLevelSelector.setSizePolicy(sizePolicy3)

        self.horizontalLayout_3.addWidget(self.displayLevelSelector)


        self.horizontalLayout_2.addLayout(self.horizontalLayout_3)


        self.horizontalLayout_5.addLayout(self.horizontalLayout_2)


        self.verticalLayout_2.addLayout(self.horizontalLayout_5)

        self.logValue = QPlainTextEdit(self.logsTab)
        self.logValue.setObjectName(u"logValue")
        font = QFont()
        font.setFamilies([u"Monospace"])
        self.logValue.setFont(font)
        self.logValue.setReadOnly(True)
        self.logValue.setPlainText(u"")

        self.verticalLayout_2.addWidget(self.logValue)

        self.horizontalLayout_4 = QHBoxLayout()
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_4.addItem(self.horizontalSpacer)

        self.clearLogsButton = QPushButton(self.logsTab)
        self.clearLogsButton.setObjectName(u"clearLogsButton")
        sizePolicy4 = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        sizePolicy4.setHorizontalStretch(0)
        sizePolicy4.setVerticalStretch(0)
        sizePolicy4.setHeightForWidth(self.clearLogsButton.sizePolicy().hasHeightForWidth())
        self.clearLogsButton.setSizePolicy(sizePolicy4)

        self.horizontalLayout_4.addWidget(self.clearLogsButton)

        self.exportLogsButton = QPushButton(self.logsTab)
        self.exportLogsButton.setObjectName(u"exportLogsButton")
        sizePolicy4.setHeightForWidth(self.exportLogsButton.sizePolicy().hasHeightForWidth())
        self.exportLogsButton.setSizePolicy(sizePolicy4)

        self.horizontalLayout_4.addWidget(self.exportLogsButton)


        self.verticalLayout_2.addLayout(self.horizontalLayout_4)

        self.tabWidget.addTab(self.logsTab, "")

        self.gridLayout.addWidget(self.tabWidget, 0, 0, 1, 1)

        MainWindow.setCentralWidget(self.centralwidget)

        self.retranslateUi(MainWindow)

        self.tabWidget.setCurrentIndex(1)


        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"MainWindow", None))
        self.userAgentsGroup.setTitle("")
        self.addUserAgentsButton.setText(QCoreApplication.translate("MainWindow", u"Add User Agents...", None))
        self.muteAllButton.setText(QCoreApplication.translate("MainWindow", u"Mute All", None))
        self.hangupAllButton.setText(QCoreApplication.translate("MainWindow", u"Hangup All", None))
        self.deleteAllButton.setText(QCoreApplication.translate("MainWindow", u"Delete All", None))
        self.userAgentSettingsGroup.setTitle("")
        self.statusGroupBox.setTitle("")
        self.userAgentStatusLabel.setText(QCoreApplication.translate("MainWindow", u"Status", None))
        self.userAgentStatusValue.setText(QCoreApplication.translate("MainWindow", u"TextLabel", None))
        self.userAgentUserLabel.setText(QCoreApplication.translate("MainWindow", u"User", None))
        self.userAgentUserValue.setText(QCoreApplication.translate("MainWindow", u"TextLabel", None))
        self.userAgentDomainLabel.setText(QCoreApplication.translate("MainWindow", u"Domain", None))
        self.userAgentDomainValue.setText(QCoreApplication.translate("MainWindow", u"TextLabel", None))
        self.deleteUAButton.setText(QCoreApplication.translate("MainWindow", u"Delete User Agent", None))
        self.callGroupBox.setTitle(QCoreApplication.translate("MainWindow", u"Call", None))
        self.callNumberLabel.setText(QCoreApplication.translate("MainWindow", u"Number", None))
        self.callNumberValue.setText(QCoreApplication.translate("MainWindow", u"Number Value", None))
        self.muteUAButton.setText(QCoreApplication.translate("MainWindow", u"Mute", None))
        self.hangupCallButton.setText(QCoreApplication.translate("MainWindow", u"Hangup", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.userAgentsTab), QCoreApplication.translate("MainWindow", u"User Agents", None))
        self.logLevelLabel.setText(QCoreApplication.translate("MainWindow", u"Log level", None))
        self.displayLevelLabel.setText(QCoreApplication.translate("MainWindow", u"Display level", None))
        self.clearLogsButton.setText(QCoreApplication.translate("MainWindow", u"Clear", None))
        self.exportLogsButton.setText(QCoreApplication.translate("MainWindow", u"Export logs...", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.logsTab), QCoreApplication.translate("MainWindow", u"Logs", None))
    # retranslateUi

