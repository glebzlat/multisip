from typing import Optional

from PySide6.QtWidgets import QWidget, QSizePolicy
from PySide6.QtCore import Signal

from ..user_agent import UserAgent
from ..ui.user_agent import Ui_UserAgent


class UserAgentWidget(QWidget, Ui_UserAgent):

    muteButtonClicked = Signal()
    hangupButtonClicked = Signal()
    deleteButtonClicked = Signal()

    def __init__(self, ua: UserAgent, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setupUi(self)
        self._connect_signals()
        self._apply_styling()
        self.uaAORValue.setText(f"{ua.user}@{ua.domain}")

    def _connect_signals(self):
        self.uaHangupButton.clicked.connect(self.hangupButtonClicked)
        self.uaMuteButton.clicked.connect(self.muteButtonClicked)
        self.uaDeleteButton.clicked.connect(self.deleteButtonClicked)

    def _apply_styling(self):
        self.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)

        self.uaActionsGroup.setStyleSheet("QGroupBox { border: none; }")
        self.uaActionsGroup.setContentsMargins(0, 0, 0, 0)
