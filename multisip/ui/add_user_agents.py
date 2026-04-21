# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'add_user_agents.ui'
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
from PySide6.QtWidgets import (QApplication, QComboBox, QGridLayout, QGroupBox,
    QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QSizePolicy, QSpinBox, QWidget)

class Ui_Form(object):
    def setupUi(self, Form):
        if not Form.objectName():
            Form.setObjectName(u"Form")
        Form.resize(320, 155)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(Form.sizePolicy().hasHeightForWidth())
        Form.setSizePolicy(sizePolicy)
        self.horizontalLayout = QHBoxLayout(Form)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.addUserAgentsGroupBox = QGroupBox(Form)
        self.addUserAgentsGroupBox.setObjectName(u"addUserAgentsGroupBox")
        self.gridLayout = QGridLayout(self.addUserAgentsGroupBox)
        self.gridLayout.setObjectName(u"gridLayout")
        self.domainLabel = QLabel(self.addUserAgentsGroupBox)
        self.domainLabel.setObjectName(u"domainLabel")

        self.gridLayout.addWidget(self.domainLabel, 0, 0, 1, 1)

        self.domainInput = QComboBox(self.addUserAgentsGroupBox)
        self.domainInput.setObjectName(u"domainInput")

        self.gridLayout.addWidget(self.domainInput, 0, 1, 1, 1)

        self.startNumberLabel = QLabel(self.addUserAgentsGroupBox)
        self.startNumberLabel.setObjectName(u"startNumberLabel")

        self.gridLayout.addWidget(self.startNumberLabel, 1, 0, 1, 1)

        self.startNumberInput = QLineEdit(self.addUserAgentsGroupBox)
        self.startNumberInput.setObjectName(u"startNumberInput")

        self.gridLayout.addWidget(self.startNumberInput, 1, 1, 1, 1)

        self.countLabel = QLabel(self.addUserAgentsGroupBox)
        self.countLabel.setObjectName(u"countLabel")

        self.gridLayout.addWidget(self.countLabel, 2, 0, 1, 1)

        self.countValue = QSpinBox(self.addUserAgentsGroupBox)
        self.countValue.setObjectName(u"countValue")
        self.countValue.setMinimum(1)

        self.gridLayout.addWidget(self.countValue, 2, 1, 1, 1)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.addUserAgentsButton = QPushButton(self.addUserAgentsGroupBox)
        self.addUserAgentsButton.setObjectName(u"addUserAgentsButton")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.addUserAgentsButton.sizePolicy().hasHeightForWidth())
        self.addUserAgentsButton.setSizePolicy(sizePolicy1)

        self.horizontalLayout_2.addWidget(self.addUserAgentsButton)

        self.cancelButton = QPushButton(self.addUserAgentsGroupBox)
        self.cancelButton.setObjectName(u"cancelButton")
        sizePolicy1.setHeightForWidth(self.cancelButton.sizePolicy().hasHeightForWidth())
        self.cancelButton.setSizePolicy(sizePolicy1)

        self.horizontalLayout_2.addWidget(self.cancelButton)


        self.gridLayout.addLayout(self.horizontalLayout_2, 3, 0, 1, 2)


        self.horizontalLayout.addWidget(self.addUserAgentsGroupBox)


        self.retranslateUi(Form)

        QMetaObject.connectSlotsByName(Form)
    # setupUi

    def retranslateUi(self, Form):
        Form.setWindowTitle(QCoreApplication.translate("Form", u"Form", None))
        self.addUserAgentsGroupBox.setTitle("")
        self.domainLabel.setText(QCoreApplication.translate("Form", u"Domain", None))
        self.startNumberLabel.setText(QCoreApplication.translate("Form", u"Start Number", None))
        self.countLabel.setText(QCoreApplication.translate("Form", u"Count", None))
        self.addUserAgentsButton.setText(QCoreApplication.translate("Form", u"Add", None))
        self.cancelButton.setText(QCoreApplication.translate("Form", u"Cancel", None))
    # retranslateUi

