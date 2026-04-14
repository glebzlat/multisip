from typing import Optional

from PySide6.QtWidgets import QWidget, QSizePolicy
from PySide6.QtCore import Signal
from PySide6.QtGui import QIcon

from ..user_agent import UserAgent
from ..ui.user_agent import Ui_UserAgent


class UserAgentWidget(QWidget, Ui_UserAgent):

    muteButtonClicked = Signal(UserAgent)
    hangupButtonClicked = Signal(UserAgent)
    deleteButtonClicked = Signal(UserAgent)

    def __init__(self, ua: UserAgent, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._ua = ua
        self.setupUi(self)
        self._connect_signals()
        self._apply_styling()
        self.uaAORValue.setText(f"{ua.user}@{ua.domain}")
        self.setActiveCall(False)

    def _connect_signals(self):
        self.uaHangupButton.clicked.connect(self._handle_hangup_button_clicked)
        self.uaMuteButton.clicked.connect(self._handle_mute_button_clicked)
        self.uaDeleteButton.clicked.connect(self._handle_delete_button_clicked)

    def _apply_styling(self):
        self.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)

        self.uaActionsGroup.setStyleSheet("QGroupBox { border: none; }")
        self.uaActionsGroup.setContentsMargins(0, 0, 0, 0)

    def setActiveCall(self, value: bool):
        self.uaHangupButton.setVisible(value)
        self.uaMuteButton.setVisible(value)

    def setEnabled(self, value: bool):
        self.uaHangupButton.setEnabled(value)
        self.uaMuteButton.setEnabled(value)
        self.uaDeleteButton.setEnabled(value)

    def setMuted(self, value: bool):
        icon = None
        if value:
            icon = QIcon(":/icons/muted.svg")
        else:
            icon = QIcon(":/icons/unmuted.svg")
        self.uaMuteButton.setIcon(icon)

    def _handle_hangup_button_clicked(self):
        self.hangupButtonClicked.emit(self._ua)

    def _handle_mute_button_clicked(self):
        self.muteButtonClicked.emit(self._ua)

    def _handle_delete_button_clicked(self):
        self.deleteButtonClicked.emit(self._ua)
