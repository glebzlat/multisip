from typing import Optional

from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Signal, QRegularExpression
from PySide6.QtGui import QRegularExpressionValidator

from ..ui.add_user_agents import Ui_Form


class AddUserAgents(QWidget, Ui_Form):

    returnData = Signal(int, int)

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setupUi(self)

        self.int_re = QRegularExpression(r"[0-9]+")
        self.regex_validator = QRegularExpressionValidator(self.int_re)

        self.startNumberInput.setValidator(self.regex_validator)
        self.addUserAgentsButton.clicked.connect(self.handle_addUserAgentsButton_clicked)
        self.cancelButton.clicked.connect(self.handle_cancelButton_clicked)

    def handle_addUserAgentsButton_clicked(self):
        start_account = int(self.startNumberInput.text())
        count = self.countValue.value()
        self.returnData.emit(start_account, count)
        self.close()

    def handle_cancelButton_clicked(self):
        self.close()

    def clear(self):
        self.startNumberInput.clear()
        self.countValue.setValue(1)

    def showClean(self):
        self.clear()
        self.show()
