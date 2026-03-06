from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import pyqtSignal, QRegularExpression
from PyQt6.QtGui import QRegularExpressionValidator

from ..ui.add_user_agents import Ui_Form


class AddUserAgents(QWidget, Ui_Form):

    returnData = pyqtSignal(int, int)

    def __init__(self):
        super().__init__()
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
