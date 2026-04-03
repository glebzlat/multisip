from __future__ import annotations

from typing import List, Optional

from PySide6.QtCore import QObject, QProcess, Signal

from ..log import get_logger


class ProcessManager(QObject):

    # Lifecycle
    started = Signal(int)  # pid
    finished = Signal(int, QProcess.ExitStatus)
    errorOccurred = Signal(str)

    # State
    runningChanged = Signal(bool)

    def __init__(
        self,
        program: str = "baresip",
        arguments: Optional[List[str]] = None,
        parent: Optional[QObject] = None,
    ):
        super().__init__(parent)

        self._log = get_logger(self.__class__.__name__)

        self._program = program
        self._arguments = arguments or []

        self._process: Optional[QProcess] = None
        self._running: bool = False

    def is_running(self) -> bool:
        return self._running

    def pid(self) -> int:
        if self._process is None:
            return 0
        return int(self._process.processId())

    def start(self) -> bool:
        if self._process is not None:
            self.errorOccurred.emit("baresip already running")
            return False

        proc = QProcess(self)
        proc.setProgram(self._program)
        proc.setArguments(self._arguments)
        print(self._program, self._arguments)

        # Important: merged output simplifies debugging/logging
        proc.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)

        # Signals
        proc.started.connect(self._on_started)
        proc.finished.connect(self._on_finished)
        proc.errorOccurred.connect(self._on_error)

        self._process = proc
        proc.start()
        return True

    def stop(self, graceful: bool = True) -> None:
        """
        graceful=True  -> terminate (SIGTERM)
        graceful=False -> kill (SIGKILL)
        """
        proc = self._process
        if proc is None:
            return

        if proc.state() == QProcess.ProcessState.NotRunning:
            self._cleanup()
            return

        if graceful:
            proc.terminate()
        else:
            proc.kill()

    def restart(self) -> None:
        self.stop(graceful=True)

        # restart after finished signal
        def _restart(*_):
            self.finished.disconnect(_restart)
            self.start()

        self.finished.connect(_restart)

    def _on_started(self) -> None:
        self._running = True
        self.runningChanged.emit(True)

        pid = self.pid()
        self.started.emit(pid)
        self._log.debug("baresip started: pid=%d", pid)

    def _on_finished(self, exit_code: int, exit_status: QProcess.ExitStatus) -> None:
        self.finished.emit(exit_code, exit_status)
        self._process.deleteLater()

        if self._running:
            self._running = False
            self.runningChanged.emit(False)

        self._log.debug("baresip stopped")

    def _on_error(self, error: QProcess.ProcessError) -> None:
        if self._process is None:
            return

        error_str = self._process.errorString()
        self.errorOccurred.emit(error_str)
        self._log.error("baresip error: %s", error_str)
