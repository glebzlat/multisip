import logging

from typing import Optional, Iterable
from dataclasses import dataclass
from datetime import datetime

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
    QGroupBox,
    QFileDialog
)
from PySide6.QtGui import QPalette, QTextCursor

from .add_user_agents import AddUserAgents
from .user_agent import UserAgentWidget
from ..user_agent import UserAgent, Status as UserAgentStatus
from ..ui.main_window import Ui_MainWindow
from ..worker import Worker
from ..config import Config
from ..baresip import Event, Operation as ProtocolOperation
from ..log import get_logger


@dataclass
class UserAgentState:
    list_item: QWidget
    widget: UserAgentWidget
    status: UserAgentStatus = UserAgentStatus.PENDING
    active_call_number: Optional[int] = None
    muted: bool = True


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
    deleteAll = Signal()
    hangupAll = Signal()
    muteAll = Signal()

    deleteUA = Signal(UserAgent)
    hangupCall = Signal(UserAgent)
    setMuteUA = Signal(UserAgent, bool)

    setLogLevel = Signal(int)
    clearLogs = Signal()
    exportLogs = Signal(str)  # path to the file

    setProcessRunning = Signal(bool)

    def __init__(self, worker: Worker, config: Config, log_handler):
        super().__init__()
        self.setupUi(self)
        self.setWindowTitle("MultiSIP")

        self._config = config

        self._log = get_logger(self.__class__.__name__)

        self._setup_widgets()
        self._connect_signals()

        self._add_uas_window = AddUserAgents()
        self._add_uas_window.setWindowTitle("MultiSIP - Add User agents")
        self._add_uas_window.returnData.connect(self._handle_add_uas_data)

        self._worker = worker
        self._setup_worker()

        self._active_ua: Optional[UserAgent] = None
        self._ua_states: dict[UserAgent, UserAgentState] = {}
        self._unmuted_ua: Optional[UserAgent] = None

        self._log_handler = log_handler
        self._n_log_lines = 0

        self.logLevelSelector.setCurrentText(self._config.log_level.name)
        self.displayLevelSelector.setCurrentText(self._config.log_level.name)

    def _connect_signals(self):
        self.addUserAgentsButton.clicked.connect(self._handle_add_uas)
        self.deleteAllButton.clicked.connect(self._handle_delete_all)
        self.hangupAllButton.clicked.connect(self._handle_hangup_all)
        self.muteAllButton.clicked.connect(self._handle_mute_all)

        self.deleteUAButton.clicked.connect(self._handle_delete_ua)
        self.muteUAButton.clicked.connect(self._handle_mute_active_ua)
        self.hangupCallButton.clicked.connect(self._handle_hangup_call_btn_clicked)

        self.logLevelSelector.activated.connect(self._handle_set_log_level)
        self.displayLevelSelector.activated.connect(self._handle_set_display_level)

        self.clearLogsButton.clicked.connect(self._handle_clear_logs)
        self.exportLogsButton.clicked.connect(self._handle_export_logs)

        self.startStopButton.clicked.connect(self._handle_start_stop)

    def _setup_widgets(self):
        self.uaScroll = QWidget(self)
        self.uaScrollLayout = QVBoxLayout(self.uaScroll)
        self.uaScrollLayout.addStretch(0)
        self.uaScroll.setLayout(self.uaScrollLayout)
        self.scrollArea.setWidget(self.uaScroll)

        self._set_active_ua(None)

        self.logLevelSelector.addItems(self._config.log_level.names())
        self.displayLevelSelector.addItems(self._config.log_level.names())

        self._set_actions_active(False)

    def _setup_worker(self):

        def connect(emitter, handler):
            emitter.connect(handler, type=Qt.ConnectionType.QueuedConnection)

        connect(self._worker.manager.callEstablished, self._handle_incoming_call)
        connect(self._worker.manager.callClosed, self._handle_call_closed)
        connect(self._worker.manager.userAgentRegistrationChanged, self._handle_reg_changed)
        connect(self._worker.manager.transactionCompletedSimple, self._handle_transaction_completed)
        connect(self._worker.manager.userAgentRemoved, self._handle_ua_removed)

        connect(self.deleteAll, self._worker.handle_delete_all)
        connect(self.hangupAll, self._worker.handle_hangup_all)
        connect(self.muteAll, self._worker.handle_mute_all)

        connect(self.deleteUA, self._worker.handle_delete_ua)
        connect(self.hangupCall, self._worker.handle_hangup_call)
        connect(self.setMuteUA, self._worker.handle_set_mute)

        connect(self.setProcessRunning, self._worker.set_running)

        connect(self._worker.process.runningChanged, self._handle_process_running)

        connect(self._worker.workerReady, self._handle_ready)

        self._worker_thread = QThread()
        self._worker.moveToThread(self._worker_thread)
        connect(self.addUserAgents, self._worker.add_uas)
        connect(self._worker.userAgentAdded, self._handle_ua_added)
        connect(self._worker.muteStateChanged, self._handle_mute_state_changed)
        self._worker_thread.start()

    def _handle_add_uas(self):
        self._add_uas_window.showClean()

    def _handle_delete_all(self):
        self.deleteAll.emit()

    def _handle_hangup_all(self):
        self.hangupAll.emit()

    def _handle_mute_all(self):
        for ua, state in self._ua_states.items():
            if state.active_call_number is None:
                continue
            self._apply_mute_state(ua, True)
        self.muteAll.emit()

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
        user_agent.deleteButtonClicked.connect(self.deleteUA)
        user_agent.muteButtonClicked.connect(self._handle_mute)
        user_agent.setMuted(True)
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
        state.active_call_number = ev.user
        state.call_number = ev.user
        state.widget.setActiveCall(True)

        if ua == self._active_ua:
            self.callGroupBox.setVisible(True)
            self.callNumberValue.setText(ev.user)

    def _handle_call_closed(self, ua: UserAgent, ev: Event):
        state = self._ua_states[ua]
        state.active_call_number = None
        self._apply_mute_state(ua, True)
        state.widget.setActiveCall(False)

        if ua == self._active_ua:
            self.callGroupBox.setVisible(False)

    def _handle_reg_changed(self, ua: UserAgent, status: UserAgentStatus):
        state = self._ua_states.get(ua)
        if state is None:
            # "Pending" register event comes before the UA is registered
            # and added to the _ua_states.
            return

        state.status = status

        if ua == self._active_ua:
            self.userAgentStatusValue.setText(state.status.name)

    def _handle_delete_ua(self):
        self.deleteUA.emit(self._active_ua)

    def _handle_hangup_call_btn_clicked(self):
        self._hangup_call(self._active_ua)

    def _handle_mute_active_ua(self):
        if self._active_ua is None:
            return
        self._handle_mute(self._active_ua)

    def _handle_mute(self, ua: UserAgent):
        state = self._ua_states[ua]
        if state.active_call_number is None:
            return

        muted = not state.muted
        self._apply_mute_state(ua, muted)
        self.setMuteUA.emit(ua, muted)

    def _handle_mute_state_changed(self, ua: UserAgent, muted: bool):
        self._apply_mute_state(ua, muted)

    def _handle_transaction_completed(self, op: ProtocolOperation, ua: UserAgent):
        if op == ProtocolOperation.HANGUP:
            self._hangup_call_ui(ua)

    def _handle_ua_removed(self, ua: UserAgent):
        if self._unmuted_ua == ua:
            self._unmuted_ua = None

        state = self._ua_states.pop(ua, None)
        if state is None:
            return
        state.list_item.deleteLater()
        if ua == self._active_ua:
            self._set_active_ua(None)

    def _handle_set_log_level(self, index: int):
        level_name = self._config.log_level.names()[index]
        log_level = self._config.log_level.from_string(level_name)
        self.setLogLevel.emit(log_level)

    def _handle_set_display_level(self, index: int):
        level_name = self._config.log_level.names()[index]
        log_level = self._config.log_level.from_string(level_name)
        self._fill_log_window(log_level)

    def _handle_clear_logs(self):
        self.logValue.clear()
        self._n_log_lines = 0
        self.clearLogs.emit()

    def _handle_export_logs(self):
        ftime = datetime.now().strftime("%Y-%m-%d_%H-%M")
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            caption="Save File",
            dir=f"multisip_{ftime}.log",
            filter="Text Files (*.txt);;All Files (*)"
        )

        if file_path is None:
            return

        self.exportLogs.emit(file_path)

    def _handle_start_stop(self):
        self.setProcessRunning.emit(not self._worker.process.is_running())

    def _handle_process_running(self, running: bool):
        if running:
            return

        self.startStopButton.setText("Start")
        self._set_actions_active(False)

        if self._unmuted_ua is not None:
            self._apply_mute_state(self._unmuted_ua, True)

        for ua, state in self._ua_states.items():
            state.widget.setEnabled(False)

            if state.active_call_number is not None:
                self._hangup_call_ui(ua, state)
                state.active_call_number = None

    def _handle_ready(self):
        self.startStopButton.setText("Stop")
        self._set_actions_active(True)
        for ua, state in self._ua_states.items():
            state.widget.setEnabled(True)

    def _set_active_ua(self, ua: Optional[UserAgent]) -> None:
        self._active_ua = ua

        visible = self._active_ua is not None
        self.statusGroupBox.setVisible(visible)
        self.deleteUAButton.setVisible(visible)
        self.callGroupBox.setVisible(visible)

        if not visible:
            return

        state = self._ua_states[ua]

        self.userAgentStatusValue.setText(state.status.name)
        self.userAgentUserValue.setText(str(ua.user))
        self.userAgentDomainValue.setText(ua.domain)

        visible = state.active_call_number is not None
        self.callGroupBox.setVisible(visible)
        if visible:
            self.callNumberValue.setText(state.active_call_number)
            self._update_active_mute_button(state)

    def _hangup_call(self, ua: UserAgent):
        state = self._ua_states[ua]
        if state.active_call_number is None:
            return

        self.hangupCall.emit(ua)

    def _hangup_call_ui(self, ua: UserAgent, state: UserAgentState):
        state.widget.setActiveCall(False)
        if ua == self._active_ua:
            self.callGroupBox.setVisible(False)

    def _apply_mute_state(self, ua: UserAgent, muted: bool) -> None:
        state = self._ua_states.get(ua)
        if state is None:
            return

        if not muted and self._unmuted_ua is not None and self._unmuted_ua != ua:
            prev_state = self._ua_states.get(self._unmuted_ua)
            if prev_state is not None:
                prev_state.muted = True
                prev_state.widget.setMuted(True)
                if self._active_ua == self._unmuted_ua and prev_state.active_call_number is not None:
                    self._update_active_mute_button(prev_state)

        state.muted = muted
        state.widget.setMuted(muted)

        if muted:
            if self._unmuted_ua == ua:
                self._unmuted_ua = None
        else:
            self._unmuted_ua = ua

        if self._active_ua == ua and state.active_call_number is not None:
            self._update_active_mute_button(state)

    def _update_active_mute_button(self, state: UserAgentState) -> None:
        self.muteUAButton.setText("Unmute" if state.muted else "Mute")

    def _fill_log_window(self, level: int):
        self.logValue.clear()
        self._n_log_lines = 0
        for line in self._log_handler.lines(level):
            self.logValue.appendHtml(f"<p>{line}</p>")
            self._n_log_lines += 1

    def _set_actions_active(self, active: bool):
        self.addUserAgentsButton.setEnabled(active)
        self.hangupAllButton.setEnabled(active)
        self.muteAllButton.setEnabled(active)
        self.deleteAllButton.setEnabled(active)
        self.deleteUAButton.setEnabled(active)

    @Slot(str)
    def handle_log_line_added(self, line: str) -> None:
        self.logValue.appendHtml(f"<p>{line}</p>")
        self._n_log_lines += 1

        max_lines = self._log_handler.max_lines
        while self._n_log_lines > max_lines:
            cursor = QTextCursor(self.logValue.document())
            cursor.movePosition(QTextCursor.Start)
            cursor.select(QTextCursor.SelectionType.BlockUnderCursor)
            cursor.removeSelectedText()
            cursor.deleteChar()
            self._n_log_lines -= 1

    def closeEvent(self, event):
        QMetaObject.invokeMethod(
            self._worker,
            "stop",
            Qt.ConnectionType.BlockingQueuedConnection
        )
        self._worker_thread.quit()
        self._worker_thread.wait()
        event.accept()
