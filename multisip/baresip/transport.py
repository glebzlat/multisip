import json
import uuid

from typing import Any, Optional

from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtNetwork import QAbstractSocket, QTcpSocket


class CtrlTcpTransport(QObject):

    connectedChanged = pyqtSignal(bool)
    responseReceived = pyqtSignal(dict)
    eventReceived = pyqtSignal(dict)
    messageReceived = pyqtSignal(dict)
    protocolError = pyqtSignal(str)
    socketError = pyqtSignal(str)

    def __init__(self, host: str, port: int, parent: Optional[QObject] = None):
        super().__init__(parent)
        self._host = host
        self._port = port
        self._socket = QTcpSocket(self)
        self._buffer = bytearray()

        self._socket.connected.connect(self._on_connected)
        self._socket.disconnected.connect(self._on_disconnected)
        self._socket.readyRead.connect(self._on_ready_read)
        self._socket.errorOccurred.connect(self._on_error)

    def connect(self) -> None:
        if self._socket.state() != QAbstractSocket.SocketState.UnconnectedState:
            self._socket.abort()
        self._socket.connectToHost(self._host, self._port)

    def disconnect(self) -> None:
        self._socket.disconnectFromHost()

    def is_connected(self) -> bool:
        return self._socket.state() == QAbstractSocket.SocketState.ConnectedState

    def send_command(self, command: str, params: Optional[str] = None, token: Optional[str] = None):
        if not self.is_connected():
            raise RuntimeError("ctrl_tcp socket is not connected")

        if token is None:
            token = str(uuid.uuid4())

        payload: dict[str, Any] = {"command": command, "token": token}
        if params is not None and params != "":
            payload["params"] = params

        blob = json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("UTF-8")
        frame = f"{len(blob)}:".encode("ascii") + blob + b","
        self._socket.write(frame)

        return token

    def _on_connected(self) -> None:
        self.connectedChanged.emit(True)

    def _on_disconnected(self) -> None:
        self.connectedChanged.emit(False)

    def _on_error(self, _err) -> None:
        self.socketError.emit(self._socket.errorString())

    def _on_ready_read(self) -> None:
        self._buffer.extend(bytes(self._socket.readAll()))

        while True:
            frame = self._try_take_netstring()
            if frame is None:
                break

            try:
                obj = json.loads(frame.decode("UTF-8"))
            except Exception as e:
                self.protocolError.emit(f"Invalid JSON frame: {e}")
                continue

            if obj.get("response") is True:
                self.responseReceived.emit(obj)
            elif obj.get("event") is True:
                self.eventReceived.emit(obj)
            elif obj.get("message") is True:
                self.messageReceived.emit(obj)
            else:
                self.protocolError.emit(f"Unknown ctrl_tcp message type: {obj!r}")

    def _try_take_netstring(self) -> Optional[bytes]:
        colon = self._buffer.find(b":")
        if colon < 0:
            return None

        len_bytes = self._buffer[:colon]
        if not len_bytes or any(b < b"0" or b > b"9" for b in len_bytes):
            self.protocolError.emit("invalid netstring length prefix")
            self._buffer.clear()
            return None

        size = int(len_bytes.decode("ascii"))
        total = colon + 1 + size + 1
        if len(self._buffer) < total:
            return None

        if self._buffer[total - 1] != ord(","):
            self.protocolError.emit("invalid netstring terminator")
            self._buffer.clear()
            return None

        payload = bytes(self._buffer[colon + 1:colon + 1 + size])
        del self._buffer[:total]
        return payload


