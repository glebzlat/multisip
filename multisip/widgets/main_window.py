from typing import Optional, Iterable
from dataclasses import dataclass, field

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QMainWindow,
    QSizePolicy,
    QSpacerItem,
    QGroupBox
)
from PySide6.QtGui import QPalette

from .add_user_agents import AddUserAgents
from .user_agent import UserAgent as UserAgentWidget
from ..user_agent import UserAgent
from ..ui.main_window import Ui_MainWindow
from ..worker import Worker
from ..config import Config


@dataclass
class UserAgentWidgetState:
    widget: QWidget
    call_actions: QWidget
    active_call_number: Optional[str] = field(default=None, init=False)


class ClickableItem(QWidget):

    clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAutoFillBackground(True)

        self._hover_palette = self.palette()
        self._hover_palette.setColor(QPalette.ColorRole.Window, self._hover_palette.color(QPalette.ColorRole.Highlight))
        self._hover_palette.setColor(QPalette.ColorRole.WindowText, self._hover_palette.color(QPalette.ColorRole.HighlightedText))

        self._inactive_palette = self.palette()

    def mousePressEvent(self, event):
        if not self.isEnabled():
            return
        self.clicked.emit()
        super().mousePressEvent(event)

    def enterEvent(self, event):
        if not self.isEnabled():
            return
        self.setPalette(self._hover_palette)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        event.accept()

    def leaveEvent(self, event):
        if not self.isEnabled():
            return
        self.setPalette(self._inactive_palette)
        self.setCursor(Qt.CursorShape.ArrowCursor)
        event.accept()


class MainWindow(QMainWindow, Ui_MainWindow):

    addUAs = Signal(int, int)  # start_account, count

    def __init__(self, worker: Worker, config: Config):
        super().__init__()
        self.setupUi(self)
        self.setWindowTitle("MultiSIP")
        self._setup_widgets()

        self._worker = worker

        self._active_ua: Optional[UserAgent] = None

        self._add_user_agent(UserAgent(490, "10.10.2.4"), 0)

    def _connect_signals(self):
        self.addUserAgentsButton.clicked.connect(self._handle_add_uas)

    def _setup_widgets(self):
        self.uaScroll = QWidget(self)
        self.uaScrollLayout = QVBoxLayout(self.uaScroll)
        self.uaScrollLayout.addStretch(0)
        self.uaScroll.setLayout(self.uaScrollLayout)
        self.scrollArea.setWidget(self.uaScroll)

    def _handle_add_uas(self):
        add_form = AddUserAgents(self)
        add_form.returnData.connect(self._handle_add_uas_data)

    def _handle_add_uas_data(self, start_account: int, count: int):
        self.addUAs.emit(start_account, count)

    def _add_user_agent(self, ua: UserAgent, at_index: int):

        def _handle_clicked():
            self._set_active_ua(ua)

        item = ClickableItem(parent=self)
        item.clicked.connect(_handle_clicked)

        layout = QHBoxLayout(item)
        item.setLayout(layout)

        user_agent = UserAgentWidget(self)
        layout.addWidget(user_agent)

        self.uaScrollLayout.insertWidget(at_index, item)

    def _set_active_ua(self, ua: UserAgent):
        self._active_ua = ua
