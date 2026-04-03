from __future__ import annotations

from typing import Any, Optional, Dict
from dataclasses import dataclass, field
from enum import StrEnum

from PySide6.QtCore import QObject, Signal

from .protocol import CtrlTcpProtocol
from ..user_agent import UserAgent


class Operation(StrEnum):
    CREATE_UA = "create_ua"
    DELETE_UA = "delete_ua"
    REQUEST_REGINFO = "request_reginfo"
    DIAL = "dial"
    MUTE = "mute"
    RESUME = "resume"
    HANGUP = "hangup"
    HANGUP_ALL = "hangup_all"
    CALLSTAT = "callstat"
    CALLFIND = "callfind"


class CtrlTcpManager(QObject):

    @dataclass(slots=True)
    class PendingRequest:
        token: str
        operation: Operation
        ua: Optional[UserAgent] = None
        params: Optional[str] = None
        meta: Dict[str, Any] = field(default_factory=dict)

    @dataclass
    class UserAgentState:
        aor: str
        created: bool = False
        registered: bool = False
        current_call_id: Optional[str] = None
        current_call_line: Optional[int] = None
        last_event: Optional[str] = None

    # Raw correlated lifecycle
    requestSent = Signal(object)                  # PendingRequest
    requestFinished = Signal(object, dict)       # PendingRequest, response
    requestTimedOut = Signal(object)             # PendingRequest
    unknownResponse = Signal(dict)

    # UA lifecycle
    userAgentAdded = Signal(object)              # UserAgent
    userAgentRemoved = Signal(object)            # UserAgent
    userAgentCreated = Signal(object, dict)      # UserAgent, response
    userAgentDeleted = Signal(object, dict)      # UserAgent, response
    userAgentRegistrationChanged = Signal(object, bool, str)  # UserAgent, registered, event_type

    # Call events
    incomingCall = Signal(object, str, str)      # UserAgent, call_id, peer_uri
    callEstablished = Signal(object, str, str)   # UserAgent, call_id, peer_uri
    callClosed = Signal(object, str, str)        # UserAgent, call_id, reason

    # Raw protocol passthrough
    eventReceived = Signal(dict)
    messageReceived = Signal(dict)

    # Errors
    managerError = Signal(str)

    def __init__(self, protocol: CtrlTcpProtocol, parent: Optional[QObject] = None):
        super().__init__(parent)
        self._p = protocol

        self._pending_requests: dict[str, CtrlTcpManager.PendingRequest] = {}
        self._sequence_by_aor: dict[str, int] = {}
        self._user_agents: dict[UserAgent, CtrlTcpManager.UserAgentState] = {}

        self._p.responseReceived.connect(self._on_response)
        self._p.eventReceived.connect(self._on_event)
        self._p.messageReceived.connect(self._on_message)

    def user_agents(self) -> list[UserAgent]:
        return [ua for ua in self._user_agents.keys()]

    def pending_request(self, token: str) -> Optional[PendingRequest]:
        return self._pending_requests.get(token)

    def pending_requests(self) -> list[PendingRequest]:
        return list(self._pending_requests.values())

    def add_user_agent(self, user: int, password: str, domain: str) -> Optional[UserAgent]:
        ua = UserAgent(user=user, password=password, domain=domain)
        aor = self._aor_of(ua)
        if aor in self._user_agents:
            self.managerError.emit(f"user agent already added: {aor}")
            return None
        self._user_agents[ua] = self.UserAgentState(ua=ua, aor=aor)
        self.userAgentAdded.emit(ua)
        return ua

    def remove_user_agent(self, ua: UserAgent) -> bool:
        state = self._user_agents.get(ua)
        if state is None:
            self.managerError.emit(f"user agent not found: {ua}")
            return False
        if state.created:
            self.managerError.emit(f"user agent still exists in baresip: {ua}")
            return False
        del self._user_agents[ua]
        aor = self._aor_of(ua)
        self._sequence_by_aor.pop(aor, None)
        self.userAgentRemoved.emit(ua)
        return True

    def create_user_agent(self, ua: UserAgent) -> None:
        state = self._user_agents.get(ua)
        acc_line = self._account_line_of(ua)
        if state is None:
            raise ValueError(f"user agent not added: {ua}")
        token = self._make_token(ua)
        rq = self.PendingRequest(
            token=token,
            operation=Operation.CREATE_UA,
            ua=ua,
            params=acc_line
        )
        self._pending_requests[token] = rq
        self._p.uanew(acc_line, token)
        self.requestSent.emit(rq)

    def delete_user_agent(self, ua: UserAgent) -> None:
        state = self._user_agents.get(ua)
        if state is None:
            raise ValueError(f"user agent not added: {ua}")
        token = self._make_token(ua)
        rq = self.PendingRequest(
            token=token,
            operation=Operation.DELETE_UA,
            ua=ua,
            params=state.aor
        )
        self._pending_requests[token] = rq
        self._p.uadel(state.aor, token)
        self.requestSent.emit(rq)

    def request_reginfo(self) -> None:
        token = self._make_global_token("reginfo")
        rq = self.PendingRequest(token=token, operation=Operation.REQUEST_REGINFO)
        self._pending_requests[token] = rq
        self._p.reginfo(token)
        self._requestSent.emit(rq)

    def dial(self, ua: UserAgent, uri: str) -> None:
        state = self._user_agents.get(ua)
        if state is None:
            raise ValueError(f"user agent not added: {ua}")
        token = self._make_token(ua)
        rq = self.PendingRequest(
            token=token,
            operation=Operation.DIAL,
            ua=ua,
            params=uri
        )
        self._pending_requests[token] = rq
        self._p.dial(uri)
        self.requestSent.emit(rq)

    def mute(self, ua: UserAgent) -> None:
        state = self._user_agents.get(ua)
        if state is None:
            raise ValueError(f"user agent not added: {ua}")
        if state.current_call_line is None:
            return
        token = self._make_token(ua)
        rq = self.PendingRequest(token=token, operation=Operation.MUTE)
        self._pending_requests[token] = rq
        self._p.mute(state.current_call_line, token)
        self.requestSent.emit(rq)

    def resume(self, ua: UserAgent) -> None:
        state = self._user_agents.get(ua)
        if state is None:
            raise ValueError(f"user agent not added: {ua}")
        if state.current_call_id is None:
            return
        token = self._make_token(ua)
        rq = self.PendingRequest(
            token=token,
            operation=Operation.RESUME,
            ua=ua,
            params=state.current_call_id
        )
        self._pending_requests[token] = rq
        self._p.resume(state.current_call_id, token)
        self.requestSent.emit(rq)

    def accept(self, ua: UserAgent) -> None:
        state = self._user_agents.get(ua)
        if state is None:
            raise ValueError(f"user agent not added: {ua}")
        if state.current_call_line is not None:
            return
        token = self._make_token(ua)
        rq = self.PendingRequest(
            token=token,
            operation=Operation.ACCEPT,
            ua=ua
        )
        self._pending_requests[token] = rq
        self._p.accept(token)
        self.requestSent(rq)

    def hangup(self, ua: UserAgent) -> None:
        state = self._user_agents.get(ua)
        if state is None:
            raise ValueError(f"user agent not added: {ua}")
        if state.current_call_line is None:
            return
        token = self._make_token(ua)
        rq = self.PendingRequest(
            token=token,
            operation=Operation.HANGUP,
            ua=ua
        )
        self._pending_requests[token] = rq
        self._p.hangup(state.current_call_id, token)
        self.requestSent(rq)

    def hangup_all(self) -> None:
        token = self._make_global_token("hangupall")
        rq = self.PendingRequest(token=token, operation=Operation.HANGUP_ALL)
        self._pending_requests[token] = rq
        self._p.hangupall(None, token)
        self.requestSent.emit(rq)

    def callstat(self) -> None:
        token = self._make_global_token("callstat")
        rq = self.PendingRequest(token=token, operation=Operation.CALLSTAT)
        self._pending_requests[token] = rq
        self._p.callstat(token)
        self.requestSent.emit(rq)

    def set_current_call(self, ua: UserAgent) -> None:
        state = self._user_agents.get(ua)
        if state is None:
            raise ValueError(f"user agent not added: {ua}")
        if state.current_call_id is None:
            return
        token = self._make_token(ua)
        rq = self.PendingRequest(
            token=token,
            operation=Operation.CALLFIND,
            ua=ua,
            params=state.current_call_id
        )
        self._pending_requests[token] = rq
        self._p.callfind(state.current_call_id, token)
        self.requestSent.emit(rq)

    def shutdown(self) -> None:
        for ua, state in self._user_agents.items():
            if state.created:
                try:
                    self.delete_user_agent(ua)
                except Exception as e:
                    self.managerError.emit(f"failed to delete {ua} during shutdown: {e}")

    def deleteLater(self) -> None:
        self.shutdown()
        super().deleteLater()

    def _on_response(self, response: dict) -> None:
        token = str(response["token"])
        pending = self._pending_requests.pop(token, None)
        if pending is None:
            self.unknownResponse.emit(response)
            return
        self._apply_response(pending, response)
        self.requestFinished.emit(pending, response)

    def _apply_response(self, request: CtrlTcpManager.PendingRequest, response: dict) -> None:
        ok = bool(response.get("ok"))

        if request.operation == Operation.CREATE_UA:
            if ok:
                state = self._user_agents[request.ua]
                state.created = True
                self.userAgentCreated.emit(request.ua, response)

        elif request.operation == Operation.DELETE_UA:
            if ok:
                state = self._user_agents[request.ua]
                state.created = False
                state.registered = False
                state.last_event = "DELETED"
                self.userAgentDeleted.emit(request.ua, response)

        elif request.operation == Operation.REQUEST_REGINFO:
            data = response.get("data")
            if ok and isinstance(data, str):
                self._update_reginfo(data)

    def _on_event(self, event: dict) -> None:
        self.eventReceived.emit(event)

        aor_value = event.get("accountaor")
        event_type_value = event.get("type")
        call_id_value = event.get("id")
        peer_uri_value = event.get("peeruri")
        param_value = event.get("param")

        aor = str(aor_value) if aor_value is not None else ""
        event_type = str(event_type_value) if event_type_value is not None else ""
        call_id = str(call_id_value) if call_id_value is not None else ""
        peer_uri = str(peer_uri_value) if peer_uri_value is not None else ""
        param = str(param_value) if param_value is not None else ""

        state = self._user_agents.get(aor)
        if state is None:
            return

        if event_type in {
            "REGISTERING",
            "REGISTER_OK",
            "REGISTER_FAIL",
            "UNREGISTERING",
            "UNREGISTER_OK",
        }:
            self._apply_registration_event(state, event_type)
            return

        if event_type == "CALL_INCOMING":
            self.incomingCall.emit(state.ua, call_id, peer_uri)
            return

        if event_type == "CALL_ESTABLISHED":
            self.callEstablished.emit(state.ua, call_id, peer_uri)
            return

        if event_type == "CALL_CLOSED":
            self.callClosed.emit(state.ua, call_id, param)
            return

    def _on_message(self, message: dict):
        self.messageReceived.emit(message)

    def _apply_registration_event(self, state: UserAgentState, event_type: str) -> None:
        registered = state.registered

        if event_type == "REGISTER_OK":
            registered = True
            state.created_in_baresip = True
        elif event_type in {"REGISTER_FAIL", "UNREGISTERING", "UNREGISTER_OK"}:
            registered = False
        elif event_type == "REGISTERING":
            registered = False
            state.created_in_baresip = True

        changed = (
            state.registered != registered
            or state.last_event != event_type
        )

        state.registered = registered
        state.last_event = event_type

        if changed:
            self.userAgentRegistrationChanged.emit(state.ua, registered, event_type)

    def _update_reginfo_from_text(self, text: str) -> None:
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        for line in lines:
            aor = self._extract_first_aor(line)
            if aor is None:
                continue

            state = self._user_agents.get(aor)
            if state is None:
                continue

            low = line.lower()
            if "registered" in low:
                registered = True
                event_type = "REGINFO_REGISTERED"
                state.created_in_baresip = True
            elif "registering" in low:
                registered = False
                event_type = "REGINFO_REGISTERING"
                state.created_in_baresip = True
            elif "failed" in low or "unregistered" in low:
                registered = False
                event_type = "REGINFO_UNREGISTERED"
            else:
                continue

            changed = (
                state.registered != registered
                or state.last_event != event_type
            )

            state.registered = registered
            state.last_event = event_type

            if changed:
                self.userAgentRegistrationChanged.emit(state.ua, registered, event_type)

    def _make_token(self, ua: UserAgent) -> str:
        aor = self._aor_of(ua)
        seq = self._sequence_by_aor.get(aor, 0) + 1
        self._sequence_by_aor[aor] = seq
        return f"{aor}:{seq}"

    def _make_global_token(self, prefix: str) -> str:
        seq = self._sequence_by_aor.get(prefix, 0) + 1
        self._sequence_by_aor[prefix] = seq
        return f"{prefix}:{seq}"

    def _ensure_known_ua(self, ua: UserAgent) -> UserAgentState:
        if (state := self._user_agents.get(ua)) is not None:
            return state
        raise ValueError(f"user agent not added: {self._aor_of(ua)}")

    @staticmethod
    def _aor_of(ua: UserAgent) -> str:
        return f"sip:{ua.user}@{ua.domain}"

    @staticmethod
    def _account_line_of(ua: UserAgent) -> str:
        return f'<sip:{ua.user}@{ua.domain}>;auth_pass="{ua.password}"'

    @staticmethod
    def _extract_first_aor(text: str) -> Optional[str]:
        start = text.find("sip:")
        if start < 0:
            return None

        end = len(text)
        for sep in (" ", "\t", ">", "]", ";", ","):
            pos = text.find(sep, start)
            if pos >= 0:
                end = min(end, pos)

        return text[start:end]
