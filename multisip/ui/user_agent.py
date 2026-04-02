# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'user_agent.ui'
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
from PySide6.QtWidgets import (QApplication, QGroupBox, QHBoxLayout, QLabel,
    QPushButton, QSizePolicy, QSpacerItem, QWidget)
import multisip.resources

class Ui_UserAgent(object):
    def setupUi(self, UserAgent):
        if not UserAgent.objectName():
            UserAgent.setObjectName(u"UserAgent")
        UserAgent.resize(234, 33)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(UserAgent.sizePolicy().hasHeightForWidth())
        UserAgent.setSizePolicy(sizePolicy)
        self.horizontalLayout_2 = QHBoxLayout(UserAgent)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.uaAORValue = QLabel(UserAgent)
        self.uaAORValue.setObjectName(u"uaAORValue")

        self.horizontalLayout_2.addWidget(self.uaAORValue)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer)

        self.uaActionsGroup = QGroupBox(UserAgent)
        self.uaActionsGroup.setObjectName(u"uaActionsGroup")
        self.horizontalLayout = QHBoxLayout(self.uaActionsGroup)
        self.horizontalLayout.setSpacing(6)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.uaMuteButton = QPushButton(self.uaActionsGroup)
        self.uaMuteButton.setObjectName(u"uaMuteButton")
        icon = QIcon()
        icon.addFile(u":/icons/unmuted.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.uaMuteButton.setIcon(icon)

        self.horizontalLayout.addWidget(self.uaMuteButton)

        self.uaHangupButton = QPushButton(self.uaActionsGroup)
        self.uaHangupButton.setObjectName(u"uaHangupButton")
        icon1 = QIcon()
        icon1.addFile(u":/icons/hangup.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.uaHangupButton.setIcon(icon1)

        self.horizontalLayout.addWidget(self.uaHangupButton)

        self.uaDeleteButton = QPushButton(self.uaActionsGroup)
        self.uaDeleteButton.setObjectName(u"uaDeleteButton")
        icon2 = QIcon()
        icon2.addFile(u":/icons/cross.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.uaDeleteButton.setIcon(icon2)

        self.horizontalLayout.addWidget(self.uaDeleteButton)


        self.horizontalLayout_2.addWidget(self.uaActionsGroup)


        self.retranslateUi(UserAgent)

        QMetaObject.connectSlotsByName(UserAgent)
    # setupUi

    def retranslateUi(self, UserAgent):
        UserAgent.setWindowTitle(QCoreApplication.translate("UserAgent", u"Form", None))
        self.uaAORValue.setText(QCoreApplication.translate("UserAgent", u"TextLabel", None))
        self.uaActionsGroup.setTitle("")
        self.uaMuteButton.setText("")
        self.uaHangupButton.setText("")
        self.uaDeleteButton.setText("")
    # retranslateUi

