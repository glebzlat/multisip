from typing import Generator

from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QMainWindow,
    QSizePolicy,
    QSpacerItem
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
    UAChangedStatusMessage
)
from ..config import Config


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

        self.dialGroupBox.setVisible(False)
        self.incomingCallGroupBox.setVisible(False)
        self.callGroupBox.setVisible(False)
        self.dialingGroupBox.setVisible(False)

        self.addUserAgentsButton.clicked.connect(self.handle_addUserAgentsButton_clicked)

        self.addUserAgentsForm = AddUserAgents()
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

        self.activeUserAgent = None

        self.config = config

    def handle_addUserAgentsButton_clicked(self):
        self.addUserAgentsForm.show()

    def handle_addUserAgentsForm_returnData(self, start_account: int, count: int):
        self.requestWorker.emit(
            AddUAsRequest(
                start_number=start_account,
                count=count,
                domain=self.config.domain
            )
        )

    def handle_worker_sendMessage(self, r: WorkerOutputMessage):
        if isinstance(r, AddUAItemMessage):
            if self.activeUserAgent is None:
                self.set_active_user_agent(r.user_agent)
            label = QLabel(f"{r.user_agent.user} @ {r.user_agent.domain}")
            item = ClickableItem()
            item.clicked.connect(lambda: self.set_active_user_agent(r.user_agent))
            layout = QVBoxLayout()
            layout.addWidget(label)
            item.setLayout(layout)
            self.userAgentsScrollVBox.insertWidget(r.append_index, item, 0, Qt.AlignmentFlag.AlignTop)
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

    def set_active_user_agent(self, user_agent: UserAgent):
        self.activeUserAgent = user_agent
        self.userAgentUserValue.setText(str(user_agent.user))
        self.userAgentDomainValue.setText(user_agent.domain)
        self.userAgentStatusValue.setText("")
        self.dialGroupBox.setVisible(True)
        self.requestWorker.emit(GetUAStatusRequest(user_agent=self.activeUserAgent))

    def closeEvent(self, ev):
        self.workerThread.quit()
        self.workerThread.wait()
        ev.accept()
