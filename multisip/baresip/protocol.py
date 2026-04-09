from __future__ import annotations

from typing import Optional

from PySide6.QtCore import QObject, Signal

from .transport import CtrlTcpTransport


class CtrlTcpProtocol(QObject):

    responseReceived = Signal(dict)
    eventReceived = Signal(dict)
    messageReceived = Signal(dict)

    def __init__(self, transport: CtrlTcpTransport, parent: Optional[QObject] = None):
        super().__init__(parent)
        self._transport = transport

        self._transport.responseReceived.connect(self.responseReceived)
        self._transport.eventReceived.connect(self.eventReceived)
        self._transport.messageReceived.connect(self.messageReceived)

    def send(self, command: str, params: Optional[str] = None, token: Optional[str] = None) -> str:
        return self._transport.send_command(command=command, params=params, token=token)

    def uanew(self, account_line: str, token: Optional[str] = None) -> str:
        return self.send("uanew", account_line, token)

    def reginfo(self, token: Optional[str] = None) -> str:
        return self.send("reginfo", None, token)

    def uadel(self, arg: Optional[str] = None, token: Optional[str] = None) -> str:
        return self.send("uadel", arg, token)

    def dial(self, uri: str, token: Optional[str] = None) -> str:
        return self.send("dial", uri, token)

    def mute(self, arg: Optional[str] = None, token: Optional[str] = None) -> str:
        return self.send("mute", arg, token)

    def hold(self, arg: Optional[str] = None, token: Optional[str] = None) -> str:
        return self.send("hold", arg, token)

    def accept(self, arg: Optional[str] = None, token: Optional[str] = None) -> str:
        return self.send("accept", arg, token)

    def resume(self, arg: Optional[str] = None, token: Optional[str] = None) -> str:
        return self.send("resume", arg, token)

    def hangup(self, arg: Optional[str] = None, token: Optional[str] = None) -> str:
        return self.send("hangup", arg, token)

    def hangupall(self, arg: Optional[str] = None, token: Optional[str] = None) -> str:
        return self.send("hangupall", arg, token)

    def callstat(self, token: Optional[str] = None) -> str:
        return self.send("callstat", None, token)

    def callfind(self, arg: str, token: Optional[str] = None) -> str:
        return self.send("callfind", arg, token)

    def listcalls(self, token: Optional[str] = None) -> str:
        return self.send("listcalls", None, token)

    def uafind(self, aor: str, token: Optional[str] = None) -> str:
        return self.send("uafind", aor, token)
