from typing import Optional, Iterable
from dataclasses import dataclass

from PySide6.QtCore import Qt, QThread, Signal, QMetaObject, Slot
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
from .user_agent import UserAgentWidget
from ..user_agent import UserAgent, Status as UserAgentStatus
from ..ui.main_window import Ui_MainWindow
from ..worker import Worker
from ..config import Config
from ..baresip import Event


@dataclass
class UserAgentState:
    list_item: QWidget
    widget: UserAgentWidget
    status: UserAgentStatus = UserAgentStatus.PENDING
    active_call_id: Optional[str] = None


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

    addUserAgents = Signal(int, int)  # start_account, count
    hangupCall = Signal(UserAgent)

    setLogLevel = Signal(int)

    def __init__(self, worker: Worker, config: Config, log_handler):
        super().__init__()
        self.setupUi(self)
        self.setWindowTitle("MultiSIP")
        self._setup_widgets()
        self._connect_signals()

        self._add_uas_window = AddUserAgents()
        self._add_uas_window.setWindowTitle("MultiSIP - Add User agents")
        self._add_uas_window.returnData.connect(self._handle_add_uas_data)

        self._worker = worker
        self._setup_worker()

        self._active_ua: Optional[UserAgent] = None
        self._ua_states: dict[UserAgent, UserAgentState] = {}

        self._log_handler = log_handler

    def _connect_signals(self):
        self.addUserAgentsButton.clicked.connect(self._handle_add_uas)

        self.hangupCallButton.clicked.connect(self._handle_hangup_call)

    def _setup_widgets(self):
        self.uaScroll = QWidget(self)
        self.uaScrollLayout = QVBoxLayout(self.uaScroll)
        self.uaScrollLayout.addStretch(0)
        self.uaScroll.setLayout(self.uaScrollLayout)
        self.scrollArea.setWidget(self.uaScroll)

        self._set_active_ua(None)

    def _setup_worker(self):
        self._worker.manager.incomingCall.connect(self._handle_incoming_call, type=Qt.ConnectionType.QueuedConnection)
        self._worker.manager.callClosed.connect(self._handle_call_closed, type=Qt.ConnectionType.QueuedConnection)

        self.hangupCall.connect(self._worker.handle_hangup_call, type=Qt.ConnectionType.QueuedConnection)

        self._worker_thread = QThread()
        self._worker.moveToThread(self._worker_thread)
        self.addUserAgents.connect(self._worker.add_uas, type=Qt.ConnectionType.QueuedConnection)
        self._worker.userAgentAdded.connect(self._handle_ua_added, type=Qt.ConnectionType.QueuedConnection)
        self._worker_thread.start()

    def _handle_add_uas(self):
        self._add_uas_window.showClean()

    def _handle_add_uas_data(self, start_account: int, count: int):
        self.addUserAgents.emit(start_account, count)

    def _handle_ua_added(self, ua: UserAgent, at_index: int):

        def _handle_clicked():
            self._set_active_ua(ua)

        item = ClickableItem(parent=self)
        item.clicked.connect(_handle_clicked)

        layout = QHBoxLayout(item)
        item.setLayout(layout)

        user_agent = UserAgentWidget(ua, self)
        user_agent.hangupButtonClicked.connect(self._hangup_call)
        layout.addWidget(user_agent)

        self.uaScrollLayout.insertWidget(at_index, item)

        self._ua_states[ua] = UserAgentState(
            list_item=item,
            widget=user_agent
        )

        if self._active_ua is None:
            self._set_active_ua(ua)

    def _handle_incoming_call(self, ua: UserAgent, ev: Event):
        state = self._ua_states[ua]
        state.active_call_id = ev.call_id
        state.widget.setActiveCall(True)

        if ua == self._active_ua:
            self.callGroupBox.setVisible(True)
            self.callNumberValue.setText(ev.user)

    def _handle_call_closed(self, ua: UserAgent, ev: Event):
        state = self._ua_states[ua]
        state.active_call_id = None
        state.widget.setActiveCall(False)

        if ua == self._active_ua:
            self.callGroupBox.setVisible(False)

    def _handle_hangup_call(self):
        self._hangup_call(self._active_ua)

    def _set_active_ua(self, ua: Optional[UserAgent]) -> None:
        self._active_ua = ua

        visible = self._active_ua is not None
        self.statusGroupBox.setVisible(visible)
        self.deleteUAButton.setVisible(visible)
        self.callGroupBox.setVisible(visible)

        if not visible:
            return

        state = self._ua_states[ua]

        self.userAgentStatusValue.setText(state.status.value)
        self.userAgentUserValue.setText(str(ua.user))
        self.userAgentDomainValue.setText(ua.domain)

        visible = state.active_call_id is not None
        self.callGroupBox.setVisible(visible)
        if visible:
            self.callNumberValue.setText(state.active_call_id)

    def _hangup_call(self, ua: UserAgent):
        state = self._ua_states[ua]
        if state.active_call_id is None:
            return

        self.hangupCall.emit(ua)
        state.widget.setActiveCall(False)

        if ua == self._active_ua:
            self.callGroupBox.setVisible(False)

    @Slot(str)
    def handle_log_line_added(self, line: str) -> None:
        self.logValue.appendHtml(f"<p>{line}</p>")

    def closeEvent(self, event):
        QMetaObject.invokeMethod(
            self._worker,
            "stop",
            Qt.ConnectionType.BlockingQueuedConnection
        )
        self._worker_thread.quit()
        self._worker_thread.wait()
        event.accept()
