from typing import Optional, Iterable
from dataclasses import dataclass, field

from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtWidgets import (
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
from PyQt6.QtGui import QPalette

from .add_user_agents import AddUserAgents
from ..user_agent import UserAgent
from ..ui.main_window import Ui_MainWindow
from ..worker import (
    AddUAsRequest,
    WorkerOutputMessage,
    AddUAItemMessage,
    AddUAFinishedMessage,
    GetUAStatusRequest,
    GetUAStatusResponse,
    UAChangedStatusMessage,
    IncomingCall,
    HangupCall,
    UserAgentHungup,
    SessionTerminated,
    RemoveUserAgent,
    UserAgentRemoved
)
from ..icon_manager import get_icon
from ..config import Config


@dataclass
class UserAgentWidgetState:
    widget: QWidget
    call_actions: QWidget
    active_call_number: Optional[str] = field(default=None, init=False)


class ClickableItem(QWidget):

    clicked = pyqtSignal()

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

    requestWorker = pyqtSignal(object)
    terminateWorker = pyqtSignal()

    def __init__(self, worker, config: Config):
        super().__init__()

        self.setupUi(self)
        self.setWindowTitle("MultiSIP")

        self.dialGroupBox.setVisible(False)
        self.incomingCallGroupBox.setVisible(False)
        self.callGroupBox.setVisible(False)
        self.dialingGroupBox.setVisible(False)

        self.hangupAllButton.clicked.connect(self.handle_hangupAllButton_clicked)
        self.deleteAllButton.clicked.connect(self.handle_deleteAllButton_clicked)
        self.addUserAgentsButton.clicked.connect(self.handle_addUserAgentsButton_clicked)

        self.addUserAgentsForm = AddUserAgents()
        self.addUserAgentsForm.setWindowTitle("MultiSIP - Add user agents")
        self.addUserAgentsForm.returnData.connect(self.handle_addUserAgentsForm_returnData)

        self.userAgentsScrollWidget = QWidget()
        self.userAgentsScrollVBox = QVBoxLayout()
        self.userAgentsScrollVBox.addStretch(0)
        self.userAgentsScrollWidget.setLayout(self.userAgentsScrollVBox)

        self.scrollArea.setWidget(self.userAgentsScrollWidget)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.scrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.worker = worker
        self.workerThread = QThread()
        self.workerThread.started.connect(self.worker.start)
        self.terminateWorker.connect(self.worker.stop)
        self.workerThread.finished.connect(self.worker.stop)
        self.worker.moveToThread(self.workerThread)
        self.worker.sendMessage.connect(self.handle_worker_sendMessage)
        self.requestWorker.connect(self.worker.receive_message)
        self.workerThread.start()

        self.statusGroupBox.setVisible(False)
        self.deleteUAButton.setVisible(False)
        self.deleteUAButton.clicked.connect(self.handle_deleteUAButton_clicked)
        self.hangupCallButton.clicked.connect(self.handle_hangupCallButton_clicked)

        self.activeUserAgent = None
        self.userAgents: dict[UserAgent, UserAgentWidgetState] = {}
        self.userAgentIter: Optional[Iterable[tuple[UserAgent, UserAgentWidgetState]]] = None

        self.config = config

    def handle_hangupAllButton_clicked(self):
        if self.userAgentIter is not None:
            return
        if not self.userAgents:
            return
        self.userAgentIter = iter(reversed(self.userAgents.items()))

        ua, state = next(self.userAgentIter)
        self.requestWorker.emit(HangupCall(user_agent=ua, hangup_all=True))

    def handle_deleteAllButton_clicked(self):
        if self.userAgentIter is not None:
            return
        if not self.userAgents:
            return
        self.userAgentIter = iter(reversed(self.userAgents.items()))

        ua, state = next(self.userAgentIter)
        self.userAgentsScrollVBox.removeWidget(state.widget)
        state.widget.deleteLater()
        self.requestWorker.emit(RemoveUserAgent(ua, remove_all=True))

        self.setActiveUserAgent(None)

    def handle_addUserAgentsButton_clicked(self):
        self.addUserAgentsForm.showClean()

    def handle_addUserAgentsForm_returnData(self, start_account: int, count: int):
        self.requestWorker.emit(
            AddUAsRequest(
                start_number=start_account,
                count=count,
                domain=self.config.domain
            )
        )

    def handle_deleteUAButton_clicked(self):
        self.deleteUserAgent(self.activeUserAgent)

    def handle_hangupCallButton_clicked(self):
        self.hangupCall(self.activeUserAgent)

    def handle_worker_sendMessage(self, r: WorkerOutputMessage):
        if isinstance(r, AddUAItemMessage):
            self.addUserAgent(r.user_agent, r.append_index)
            return

        if isinstance(r, AddUAFinishedMessage):
            for widget in self.userAgentsScrollVBox.children():
                widget.setEnabled(True)

        if isinstance(r, GetUAStatusResponse):
            assert r.user_agent == self.activeUserAgent
            self.userAgentStatusValue.setText(r.status.name)

        if isinstance(r, UAChangedStatusMessage):
            if r.user_agent == self.activeUserAgent:
                self.userAgentStatusValue.setText(r.status.name)

        if isinstance(r, IncomingCall):
            state = self.userAgents[r.user_agent]
            state.active_call_number = r.call_number
            state.call_actions.setVisible(True)
            if r.user_agent == self.activeUserAgent:
                self.callGroupBox.setVisible(True)
                self.callNumberValue.setText(r.call_number)

        if isinstance(r, SessionTerminated):
            state = self.userAgents[r.user_agent]
            state.active_call_number = None
            state.call_actions.setVisible(False)
            if r.user_agent == self.activeUserAgent:
                self.callGroupBox.setVisible(False)
                self.callNumberValue.setText("")

        if isinstance(r, UserAgentRemoved):
            if not r.remove_all:
                return
            try:
                ua, state = next(self.userAgentIter)
                self.userAgentsScrollVBox.removeWidget(state.widget)
                state.widget.deleteLater()
                self.requestWorker.emit(RemoveUserAgent(ua, remove_all=True))
            except StopIteration:
                self.userAgents.clear()
                self.userAgentIter = None

        if isinstance(r, UserAgentHungup):
            if not r.hangup_all:
                return
            try:
                ua, state = next(self.userAgentIter)
                self.requestWorker.emit(HangupCall(ua, hangup_all=True))
            except StopIteration:
                self.userAgentIter = None

    def setActiveUserAgent(self, user_agent: Optional[UserAgent]):
        self.activeUserAgent = user_agent
        visible = self.activeUserAgent is not None

        self.statusGroupBox.setVisible(visible)
        self.deleteUAButton.setVisible(visible)

        if user_agent is None:
            return

        self.userAgentUserValue.setText(str(user_agent.user))
        self.userAgentDomainValue.setText(user_agent.domain)
        self.userAgentStatusValue.setText("")
        self.requestWorker.emit(GetUAStatusRequest(user_agent=self.activeUserAgent))

        state = self.userAgents[user_agent]
        if state.active_call_number:
            self.callGroupBox.setVisible(True)
            self.callNumberValue.setText(state.active_call_number)
        else:
            self.callGroupBox.setVisible(False)

    def hangupCall(self, ua: UserAgent):
        self.requestWorker.emit(HangupCall(ua))
        state = self.userAgents[ua]
        state.active_call_number = None
        state.call_actions.setVisible(False)
        if ua == self.activeUserAgent:
            self.callGroupBox.setVisible(False)

    def deleteUserAgent(self, ua: UserAgent):
        state = self.userAgents[ua]
        self.userAgentsScrollVBox.removeWidget(state.widget)
        state.widget.deleteLater()
        self.requestWorker.emit(RemoveUserAgent(self.activeUserAgent))
        del self.userAgents[ua]

        prev_ua = self.findPreviousUserAgent(ua)
        self.setActiveUserAgent(prev_ua)

    def addUserAgent(self, user_agent: UserAgent, append_index: int):
        item = ClickableItem()
        item.clicked.connect(lambda: self.setActiveUserAgent(user_agent))

        layout = QHBoxLayout()
        item.setLayout(layout)

        label = QLabel(f"{user_agent.user} @ {user_agent.domain}")
        layout.addWidget(label)

        spacer = QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        layout.addItem(spacer)

        group = QGroupBox()
        group.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)
        group.setStyleSheet("QGroupBox { border: none; }")
        group.setVisible(False)
        group_layout = QHBoxLayout()
        group_layout.setContentsMargins(0, 0, 0, 0)
        group.setLayout(group_layout)

        hangupButton = QPushButton()
        hangupButton.setIcon(get_icon("hangup"))
        hangupButton.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        hangupButton.clicked.connect(lambda: self.hangupCall(user_agent))
        group_layout.addWidget(hangupButton)

        muteButton = QPushButton()
        muteButton.setIcon(get_icon("unmuted"))
        muteButton.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        group_layout.addWidget(muteButton)

        layout.addWidget(group)

        deleteButton = QPushButton()
        deleteButton.setIcon(get_icon("cross"))
        deleteButton.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        deleteButton.clicked.connect(lambda: self.deleteUserAgent(user_agent))
        layout.addWidget(deleteButton)

        self.userAgentsScrollVBox.insertWidget(append_index, item, 0, Qt.AlignmentFlag.AlignTop)

        self.userAgents[user_agent] = UserAgentWidgetState(widget=item, call_actions=group)

        if self.activeUserAgent is None:
            self.setActiveUserAgent(user_agent)

    def findPreviousUserAgent(self, user_agent: UserAgent) -> Optional[UserAgent]:
        prev = None
        for ua in self.userAgents.keys():
            if ua == user_agent:
                break
            prev = ua
        return prev

    def closeEvent(self, ev):
        self.workerThread.quit()
        self.workerThread.wait()
        ev.accept()
