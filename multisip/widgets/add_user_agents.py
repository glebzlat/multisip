from typing import Optional

from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Signal, QRegularExpression, Slot, QEvent, QObject, Qt
from PySide6.QtGui import QRegularExpressionValidator, QKeyEvent

from ..ui.add_user_agents import Ui_Form


class AddUserAgents(QWidget, Ui_Form):

    returnData = Signal(int, int)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setupUi(self)

        self.int_re = QRegularExpression(r"[0-9]+")
        self.regex_validator = QRegularExpressionValidator(self.int_re)

        self.startNumberInput.setValidator(self.regex_validator)
        self.startNumberInput.textChanged.connect(self.handle_startNumberInput_textChanged)

        self.addUserAgentsButton.setEnabled(False)
        self.addUserAgentsButton.clicked.connect(self.handle_addUserAgentsButton_clicked)
        self.cancelButton.clicked.connect(self.handle_cancelButton_clicked)
        self.addUserAgentsButton.setAutoDefault(True)
        self.cancelButton.setAutoDefault(False)

        for widget in (
            self,
            self.startNumberInput,
            self.countValue,
            self.addUserAgentsButton,
            self.cancelButton,
        ):
            widget.installEventFilter(self)

    @Slot(str)
    def handle_startNumberInput_textChanged(self, text: str) -> None:
        enable_add_button = len(text) != 0
        self.addUserAgentsButton.setEnabled(enable_add_button)

    @Slot()
    def handle_addUserAgentsButton_clicked(self) -> None:
        start_account = int(self.startNumberInput.text())
        count = self.countValue.value()
        self.returnData.emit(start_account, count)
        self.close()

    @Slot()
    def handle_cancelButton_clicked(self) -> None:
        self.close()

    def clear(self) -> None:
        self.startNumberInput.clear()
        self.countValue.setValue(1)

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if event.type() != QEvent.Type.KeyPress:
            return super().eventFilter(watched, event)

        key_event = event if isinstance(event, QKeyEvent) else None
        if key_event is None:
            return super().eventFilter(watched, event)

        if key_event.key() == Qt.Key.Key_Escape:
            self.close()
            return True

        if key_event.key() not in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            return super().eventFilter(watched, event)

        if watched is self.cancelButton:
            self.close()
            return True

        if watched is self.addUserAgentsButton and self._is_input_valid():
            self.handle_addUserAgentsButton_clicked()
            return True

        if watched in (self, self.startNumberInput, self.countValue) and self._is_input_valid():
            self.handle_addUserAgentsButton_clicked()
            return True

        return super().eventFilter(watched, event)

    def _is_input_valid(self) -> bool:
        return len(self.startNumberInput.text()) != 0

    def show(self, start_from_number: Optional[int]) -> None:
        self.clear()
        if start_from_number is not None:
            self.startNumberInput.setText(str(start_from_number))
        self.startNumberInput.setFocus()
        super().show()
