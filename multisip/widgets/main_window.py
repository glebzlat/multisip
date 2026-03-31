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
from ..worker import Worker
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

    def __init__(self, worker: Worker, config: Config):
        super().__init__()

        self.setupUi(self)
        self.setWindowTitle("MultiSIP")

